# Eksporterer en PPTX til PDF og PNG pr. dias via PowerPoint.
# Brug: powershell -File tools/export_slides.ps1 <pptx> <pdf> <png-mappe>
param([string]$Pptx, [string]$Pdf, [string]$PngDir)
$pp = New-Object -ComObject PowerPoint.Application
try {
  $pr = $pp.Presentations.Open($Pptx, $true, $false, $false)
  $pr.SaveAs($Pdf, 32)   # 32 = ppSaveAsPDF
  foreach ($s in $pr.Slides) { $s.Export((Join-Path $PngDir ("slide-{0:D2}.png" -f $s.SlideIndex)), 'PNG', 1920, 1072) }
  $pr.Close()
} finally { $pp.Quit() }
