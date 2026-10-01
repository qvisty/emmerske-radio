# Kører Windows' indbyggede OCR (dansk) på et billede og skriver linjer med
# ord-koordinater som JSON.  Brug:  powershell -File tools/ocr.ps1 <billede> <ud.json>
param([string]$ImagePath, [string]$OutPath)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$type) {
  $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result
}

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path $ImagePath).Path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

$lang = New-Object Windows.Globalization.Language 'da'
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])

$lines = foreach ($l in $result.Lines) {
  [pscustomobject]@{
    text  = $l.Text
    words = @(foreach ($w in $l.Words) {
      [pscustomobject]@{ t = $w.Text; x = $w.BoundingRect.X; y = $w.BoundingRect.Y; w = $w.BoundingRect.Width; h = $w.BoundingRect.Height }
    })
  }
}
$angle = if ($result.TextAngle -ne $null) { [double]$result.TextAngle } else { 0.0 }
$json = ConvertTo-Json -InputObject ([pscustomobject]@{ angle = $angle; width = $bitmap.PixelWidth; height = $bitmap.PixelHeight; lines = @($lines) }) -Depth 6
[System.IO.File]::WriteAllText($OutPath, $json, (New-Object System.Text.UTF8Encoding $false))
