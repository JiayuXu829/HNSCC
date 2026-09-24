$ErrorActionPreference = 'Stop'
$root = (Resolve-Path '.').Path
$pptPath = Join-Path $root 'trust-hn\manuscript\pattern_surv_hn_springer_nature\tmp\pptx-edit\figure1_pattern_surv_hn_framework.pptx'
$pdfPath = Join-Path $root 'trust-hn\manuscript\pattern_surv_hn_springer_nature\tmp\pptx-edit\figure1_pattern_surv_hn_framework_powerpoint.pdf'
$application = New-Object -ComObject PowerPoint.Application
$presentation = $null
try {
    $presentation = $application.Presentations.Open($pptPath, $true, $false, $false)
    $presentation.SaveAs($pdfPath, 32)
} finally {
    if ($presentation -ne $null) { $presentation.Close() }
    $application.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($application)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
Write-Output $pdfPath
