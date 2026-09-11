$ErrorActionPreference = "Stop"

# 1. Habilitar acceso programatico al proyecto VBA (necesario para inyectar la macro)
$secPath = "HKCU:\Software\Microsoft\Office\16.0\Excel\Security"
if (-not (Test-Path $secPath)) { New-Item -Path $secPath -Force | Out-Null }
New-ItemProperty -Path $secPath -Name "AccessVBOM" -Value 1 -PropertyType DWORD -Force | Out-Null
New-ItemProperty -Path $secPath -Name "VBAWarnings" -Value 1 -PropertyType DWORD -Force | Out-Null

# 2. Rutas
$outDir = "C:\Apps\vales-salida-io\reportes"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$outFile = Join-Path $outDir "Reporte_Vales_Material.xlsm"
if (Test-Path $outFile) { Remove-Item $outFile -Force }

# 3. Codigo VBA
$vba = @'
Option Explicit

' Mapa: nombre de hoja -> nombre de vista en PostgreSQL
Private Function Vistas() As Variant
    Vistas = Array( _
        Array("vista_vales", "vista_vales"), _
        Array("v_movimientos", "v_movimientos"), _
        Array("vista_materiales", "vista_materiales"), _
        Array("v_discrepancias", "v_discrepancias"), _
        Array("v_rechazos_cancelaciones", "v_rechazos_cancelaciones"), _
        Array("v_bitacora_eventos", "v_bitacora_eventos") _
    )
End Function

' Construye la cadena de conexion ODBC leyendo la hoja Config
Private Function ConnString() As String
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Worksheets("Config")
    Dim host As String, port As String, db As String, usr As String, pwd As String
    host = CStr(ws.Range("B2").Value)
    port = CStr(ws.Range("B3").Value)
    db = CStr(ws.Range("B4").Value)
    usr = CStr(ws.Range("B5").Value)
    pwd = CStr(ws.Range("B6").Value)
    ConnString = "Driver={PostgreSQL Unicode(x64)};Server=" & host & ";Port=" & port & _
                 ";Database=" & db & ";Uid=" & usr & ";Pwd=" & pwd & ";"
End Function

' Refresca una hoja desde su vista. Devuelve True si tuvo exito.
Private Function RefreshSheet(sheetName As String, viewName As String, ByRef errMsg As String) As Boolean
    Dim cn As Object, rs As Object, ws As Worksheet, c As Long
    On Error GoTo fail
    Set ws = ThisWorkbook.Worksheets(sheetName)
    Set cn = CreateObject("ADODB.Connection")
    cn.Open ConnString()
    Set rs = CreateObject("ADODB.Recordset")
    rs.Open "SELECT * FROM " & viewName, cn, 3, 1
    ws.Cells.Clear
    For c = 0 To rs.Fields.Count - 1
        ws.Cells(1, c + 1).Value = rs.Fields(c).Name
    Next c
    ws.Range(ws.Cells(1, 1), ws.Cells(1, rs.Fields.Count)).Font.Bold = True
    ws.Range(ws.Cells(1, 1), ws.Cells(1, rs.Fields.Count)).Interior.Color = RGB(31, 78, 121)
    ws.Range(ws.Cells(1, 1), ws.Cells(1, rs.Fields.Count)).Font.Color = RGB(255, 255, 255)
    If Not rs.EOF Then ws.Cells(2, 1).CopyFromRecordset rs
    rs.Close: cn.Close
    On Error Resume Next
    ws.Rows(1).AutoFilter
    ws.Columns.AutoFit
    On Error GoTo 0
    RefreshSheet = True
    Exit Function
fail:
    errMsg = errMsg & " - " & sheetName & ": " & Err.Description & vbCrLf
    On Error Resume Next
    If Not rs Is Nothing Then If rs.State = 1 Then rs.Close
    If Not cn Is Nothing Then If cn.State = 1 Then cn.Close
    RefreshSheet = False
End Function

' Refresca todas las hojas SIN mostrar mensajes (uso interno/programatico)
Public Sub RefreshAllSilent()
    Dim arr As Variant, i As Long, errMsg As String
    Application.ScreenUpdating = False
    arr = Vistas()
    For i = LBound(arr) To UBound(arr)
        RefreshSheet CStr(arr(i)(0)), CStr(arr(i)(1)), errMsg
    Next i
    ThisWorkbook.Worksheets("Config").Range("B9").Value = "Ultima actualizacion: " & Format(Now, "yyyy-mm-dd hh:nn:ss")
    Application.ScreenUpdating = True
End Sub

' Boton "Actualizar datos"
Public Sub RefreshAll()
    Dim arr As Variant, i As Long, errMsg As String, okCount As Long
    Application.ScreenUpdating = False
    arr = Vistas()
    For i = LBound(arr) To UBound(arr)
        If RefreshSheet(CStr(arr(i)(0)), CStr(arr(i)(1)), errMsg) Then okCount = okCount + 1
    Next i
    ThisWorkbook.Worksheets("Config").Range("B9").Value = "Ultima actualizacion: " & Format(Now, "yyyy-mm-dd hh:nn:ss")
    Application.ScreenUpdating = True
    If Len(errMsg) > 0 Then
        MsgBox "Actualizadas " & okCount & " hoja(s)." & vbCrLf & vbCrLf & "Errores:" & vbCrLf & errMsg, vbExclamation, "Reporte de Vales"
    Else
        MsgBox "Actualizacion completa: " & okCount & " hoja(s).", vbInformation, "Reporte de Vales"
    End If
End Sub
'@

# 4. Automatizacion de Excel
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$excel.ScreenUpdating = $false

try {
    $wb = $excel.Workbooks.Add()

    # Dejar una sola hoja base y renombrarla a Config
    while ($wb.Worksheets.Count -gt 1) { $wb.Worksheets.Item($wb.Worksheets.Count).Delete() }
    $cfg = $wb.Worksheets.Item(1)
    $cfg.Name = "Config"

    # Hoja Config
    $cfg.Range("A1").Value2 = "Parametro"
    $cfg.Range("B1").Value2 = "Valor"
    $cfg.Range("A2").Value2 = "Host";          $cfg.Range("B2").Value2 = "localhost"
    $cfg.Range("A3").Value2 = "Puerto";        $cfg.Range("B3").Value2 = "5432"
    $cfg.Range("A4").Value2 = "Base de datos"; $cfg.Range("B4").Value2 = "bpta_db_VALES_MATERIAL"
    $cfg.Range("A5").Value2 = "Usuario";       $cfg.Range("B5").Value2 = "hocejo"
    $cfg.Range("A6").Value2 = "Password";      $cfg.Range("B6").Value2 = "Vales.2024"
    $cfg.Range("A9").Value2 = "Estado"
    $cfg.Range("A1:B1").Font.Bold = $true
    $cfg.Range("A1:B1").Interior.Color = 7951391   # RGB(31,78,121) = 0x7B4E1F -> BGR
    $cfg.Range("A1:B1").Font.Color = 16777215
    $cfg.Range("A1:A9").Font.Bold = $true
    $cfg.Columns.Item(1).ColumnWidth = 18
    $cfg.Columns.Item(2).ColumnWidth = 32
    $cfg.Range("D2").Value2 = "Notas:"
    $cfg.Range("D3").Value2 = "Host segun equipo: localhost (servidor), 26.32.18.150 (VPN), 192.168.1.10 (LAN)"
    $cfg.Range("D4").Value2 = "Pulsa el boton 'Actualizar datos' para recargar todas las hojas."

    # Crear una hoja por vista
    $views = @("vista_vales","v_movimientos","vista_materiales","v_discrepancias","v_rechazos_cancelaciones","v_bitacora_eventos")
    foreach ($v in $views) {
        $ws = $wb.Worksheets.Add([System.Reflection.Missing]::Value, $wb.Worksheets.Item($wb.Worksheets.Count))
        $ws.Name = $v
    }

    # Boton en Config -> RefreshAll
    $btn = $cfg.Buttons().Add(230, 15, 130, 40)
    $btn.Caption = "Actualizar datos"
    $btn.OnAction = "RefreshAll"
    $btn.Font.Size = 11
    $btn.Font.Bold = $true

    # Inyectar el modulo VBA
    $vbComp = $wb.VBProject.VBComponents.Add(1)   # 1 = vbext_ct_StdModule
    $vbComp.Name = "modVales"
    $vbComp.CodeModule.AddFromString($vba)

    # Poblar los datos por primera vez
    $excel.Run("RefreshAllSilent") | Out-Null

    # Activar la hoja principal
    $wb.Worksheets.Item("vista_vales").Activate()

    # Guardar como .xlsm (FileFormat 52 = xlOpenXMLWorkbookMacroEnabled)
    $wb.SaveAs($outFile, 52)
    $wb.Close($false)
    Write-Output "OK: archivo generado en $outFile"
}
finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
