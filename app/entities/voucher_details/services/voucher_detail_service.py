"""
VoucherDetail Service
Lógica de negocio y validaciones
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from app.entities.voucher_details.repositories.voucher_detail_repository import VoucherDetailRepository
from app.entities.voucher_details.schemas.voucher_detail_schemas import (
    VoucherDetailCreate,
    VoucherDetailUpdate,
    VoucherDetailResponse,
    VoucherDetailWithProduct,
    ProductMatchResponse,
    ProductMatchesFound
)
from app.entities.vouchers.repositories.voucher_repository import VoucherRepository
from app.entities.products.models.product import Product, ProductCategoryEnum
from app.entities.voucher_details.models.voucher_detail import VoucherDetail
from app.shared.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    BusinessRuleError
)


class VoucherDetailService:
    """
    Servicio de VoucherDetail con lógica de auto-cache.

    Características:
    - Validación de 20 líneas máximo
    - Búsqueda automática por similitud
    - Auto-creación de productos en cache
    - Incremento automático de usage_count
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = VoucherDetailRepository(db)
        self.voucher_repository = VoucherRepository(db)

    def _validate_voucher_exists(self, voucher_id: int):
        """Valida que el vale exista y esté activo"""
        voucher = self.voucher_repository.get_by_id(voucher_id)
        if not voucher:
            raise EntityNotFoundError("Voucher", voucher_id)

        if not voucher.is_active or voucher.is_deleted:
            raise BusinessRuleError(
                f"El vale {voucher_id} no está activo o fue eliminado",
                details={"voucher_id": voucher_id}
            )

        return voucher

    def _validate_max_lines(self, voucher_id: int, exclude_id: Optional[int] = None):
        """Valida que no se exceda el límite de 20 líneas"""
        current_count = self.repository.count_by_voucher(voucher_id)

        # Si estamos actualizando, no contar la línea actual
        if exclude_id:
            current_count -= 1

        if current_count >= 20:
            raise EntityValidationError(
                "VoucherDetail",
                {"line_number": "Máximo 20 líneas por vale. Límite alcanzado."}
            )

    def _validate_line_number_unique(
        self,
        voucher_id: int,
        line_number: int,
        exclude_id: Optional[int] = None
    ):
        """Valida que el line_number sea único en el vale"""
        if self.repository.exists_line_number(voucher_id, line_number, exclude_id):
            raise EntityValidationError(
                "VoucherDetail",
                {"line_number": f"El número de línea {line_number} ya existe en este vale"}
            )

    def _search_similar_products(self, item_name: str, limit: int = 10) -> List[Product]:
        """Busca productos similares por nombre"""
        return self.repository.search_similar_products(item_name, limit)

    def _auto_create_product(
        self,
        item_name: str,
        unit_of_measure: str,
        item_description: Optional[str] = None,
        created_by_id: Optional[int] = None
    ) -> Product:
        """
        Auto-crea un producto en el cache.

        Args:
            item_name: Nombre del producto
            unit_of_measure: Unidad de medida
            item_description: Descripción opcional
            created_by_id: ID del usuario que crea

        Returns:
            Producto creado
        """
        # Generar código auto con timestamp
        auto_code = f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        new_product = Product(
            name=item_name.strip(),
            code=auto_code,
            description=item_description,
            category=ProductCategoryEnum.OTHER,  # DEFAULT
            unit_of_measure=unit_of_measure,
            usage_count=1,  # Inicia en 1
            is_active=True,
            is_deleted=False,
            created_by=created_by_id
        )

        self.db.add(new_product)
        self.db.flush()  # Para obtener el ID sin commit

        return new_product

    def _increment_product_usage(self, product_id: int):
        """Incrementa el contador de uso de un producto"""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.usage_count += 1
            self.db.flush()

    def create(
        self,
        detail_data: VoucherDetailCreate,
        created_by_id: Optional[int] = None,
        skip_similarity_search: bool = False
    ) -> Union[VoucherDetailWithProduct, ProductMatchesFound]:
        """
        Crea un detalle de vale con lógica inteligente de auto-cache.

        Flujo:
        1. Validar que vale exista y no exceda 20 líneas
        2. Si product_id se proporciona → usar ese producto
        3. Si no, buscar productos similares por item_name
        4. Si encuentra matches → devolver para selección (ProductMatchesFound)
        5. Si no encuentra O skip_similarity_search=True → auto-crear producto
        6. Incrementar usage_count del producto
        7. Crear detalle

        Args:
            detail_data: Datos del detalle
            created_by_id: ID del usuario
            skip_similarity_search: Si True, salta búsqueda y auto-crea directo

        Returns:
            VoucherDetailWithProduct O ProductMatchesFound (si hay matches)
        """
        # 1. Validaciones iniciales
        self._validate_voucher_exists(detail_data.voucher_id)
        self._validate_max_lines(detail_data.voucher_id)
        self._validate_line_number_unique(detail_data.voucher_id, detail_data.line_number)

        product_id = detail_data.product_id
        auto_created = False

        # 2. Lógica de producto
        if not product_id and not skip_similarity_search:
            # Buscar productos similares
            similar_products = self._search_similar_products(detail_data.item_name)

            if similar_products:
                # Devolver matches para selección
                matches = [
                    ProductMatchResponse(
                        id=p.id,
                        name=p.name,
                        code=p.code,
                        category=p.category.value if p.category else None,
                        unit_of_measure=p.unit_of_measure,
                        usage_count=p.usage_count,
                        description=p.description
                    )
                    for p in similar_products
                ]

                return ProductMatchesFound(
                    matches=matches,
                    search_term=detail_data.item_name
                )

        # 3. Auto-crear producto si no se encontró
        if not product_id:
            new_product = self._auto_create_product(
                item_name=detail_data.item_name,
                unit_of_measure=detail_data.unit_of_measure,
                item_description=detail_data.item_description,
                created_by_id=created_by_id
            )
            product_id = new_product.id
            auto_created = True

        # 4. Incrementar usage_count
        self._increment_product_usage(product_id)

        # 5. Crear detalle
        detail_dict = detail_data.model_dump(exclude_unset=True)
        detail_dict["product_id"] = product_id
        detail_dict["created_by"] = created_by_id

        new_detail = self.repository.create(detail_dict)

        # 6. Preparar respuesta con info de producto
        product = self.db.query(Product).filter(Product.id == product_id).first()

        response = VoucherDetailWithProduct(
            id=new_detail.id,
            voucher_id=new_detail.voucher_id,
            product_id=new_detail.product_id,
            line_number=new_detail.line_number,
            item_name=new_detail.item_name,
            item_description=new_detail.item_description,
            quantity=new_detail.quantity,
            unit_of_measure=new_detail.unit_of_measure,
            serial_number=new_detail.serial_number,
            part_number=new_detail.part_number,
            notes=new_detail.notes,
            is_active=new_detail.is_active,
            created_at=new_detail.created_at,
            updated_at=new_detail.updated_at,
            product_name=product.name if product else None,
            product_code=product.code if product else None,
            product_category=product.category.value if product and product.category else None,
            auto_created=auto_created
        )

        return response

    def get_by_id(self, detail_id: int) -> VoucherDetail:
        """Obtiene un detalle por ID"""
        detail = self.repository.get_by_id(detail_id)
        if not detail:
            raise EntityNotFoundError("VoucherDetail", detail_id)
        return detail

    def get_by_voucher(self, voucher_id: int) -> List[VoucherDetailWithProduct]:
        """Obtiene todas las líneas de un vale con info de productos"""
        self._validate_voucher_exists(voucher_id)

        details = self.repository.get_by_voucher_with_products(voucher_id)

        # Convertir a schema con info de producto
        result = []
        for detail in details:
            product = detail.product
            result.append(
                VoucherDetailWithProduct(
                    id=detail.id,
                    voucher_id=detail.voucher_id,
                    product_id=detail.product_id,
                    line_number=detail.line_number,
                    item_name=detail.item_name,
                    item_description=detail.item_description,
                    quantity=detail.quantity,
                    unit_of_measure=detail.unit_of_measure,
                    serial_number=detail.serial_number,
                    part_number=detail.part_number,
                    notes=detail.notes,
                    is_active=detail.is_active,
                    created_at=detail.created_at,
                    updated_at=detail.updated_at,
                    product_name=product.name if product else None,
                    product_code=product.code if product else None,
                    product_category=product.category.value if product and product.category else None,
                    auto_created=False
                )
            )

        return result

    def update(
        self,
        detail_id: int,
        detail_data: VoucherDetailUpdate,
        updated_by_id: Optional[int] = None
    ) -> VoucherDetailWithProduct:
        """Actualiza un detalle"""
        detail = self.get_by_id(detail_id)

        # Validar line_number único si se está cambiando
        if detail_data.line_number and detail_data.line_number != detail.line_number:
            self._validate_line_number_unique(
                detail.voucher_id,
                detail_data.line_number,
                exclude_id=detail_id
            )

        # Actualizar
        update_dict = detail_data.model_dump(exclude_unset=True)
        update_dict["updated_by"] = updated_by_id

        updated_detail = self.repository.update(detail_id, update_dict)

        # Respuesta con producto
        product = updated_detail.product
        return VoucherDetailWithProduct(
            id=updated_detail.id,
            voucher_id=updated_detail.voucher_id,
            product_id=updated_detail.product_id,
            line_number=updated_detail.line_number,
            item_name=updated_detail.item_name,
            item_description=updated_detail.item_description,
            quantity=updated_detail.quantity,
            unit_of_measure=updated_detail.unit_of_measure,
            serial_number=updated_detail.serial_number,
            part_number=updated_detail.part_number,
            notes=updated_detail.notes,
            is_active=updated_detail.is_active,
            created_at=updated_detail.created_at,
            updated_at=updated_detail.updated_at,
            product_name=product.name if product else None,
            product_code=product.code if product else None,
            product_category=product.category.value if product and product.category else None,
            auto_created=False
        )

    def delete(self, detail_id: int, deleted_by_id: Optional[int] = None):
        """Elimina (soft delete) un detalle"""
        detail = self.get_by_id(detail_id)
        self.repository.delete(detail_id, soft_delete=True)

    def search_products(self, search_term: str, limit: int = 10) -> List[ProductMatchResponse]:
        """
        Endpoint auxiliar para buscar productos.
        Útil para autocomplete en frontend.
        """
        products = self._search_similar_products(search_term, limit)

        return [
            ProductMatchResponse(
                id=p.id,
                name=p.name,
                code=p.code,
                category=p.category.value if p.category else None,
                unit_of_measure=p.unit_of_measure,
                usage_count=p.usage_count,
                description=p.description
            )
            for p in products
        ]
