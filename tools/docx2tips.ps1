param(
    [Parameter(Mandatory=$true)]
    [string]$DocxPath,
    [Parameter(Mandatory=$true)]
    [string]$ItemId,
    [int]$MaxWidth = 800,
    [int]$Quality  = 80
)

$ErrorActionPreference = "Stop"

function Save-CompressedImage {
    param([string]$SrcPath, [string]$DestPath)
    Add-Type -AssemblyName System.Drawing
    $orig = [System.Drawing.Image]::FromFile($SrcPath)
    $w = $orig.Width; $h = $orig.Height
    if ($w -gt $MaxWidth) { $h = [int]($h * $MaxWidth / $w); $w = $MaxWidth }
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g   = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.DrawImage($orig, 0, 0, $w, $h)
    $codec  = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
    $params = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]$Quality)
    $bmp.Save($DestPath, $codec, $params)
    $orig.Dispose(); $bmp.Dispose(); $g.Dispose()
}

$tempDir  = Join-Path $env:TEMP "docx2tips_$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $fullPath = (Resolve-Path $DocxPath).Path
    [System.IO.Compression.ZipFile]::ExtractToDirectory($fullPath, $tempDir)

    $docXml  = [xml](Get-Content (Join-Path $tempDir "word\document.xml") -Encoding UTF8)
    $relsXml = [xml](Get-Content (Join-Path $tempDir "word\_rels\document.xml.rels") -Encoding UTF8)

    $ns = New-Object System.Xml.XmlNamespaceManager($docXml.NameTable)
    $ns.AddNamespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")
    $ns.AddNamespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")

    $relMap = @{}
    foreach ($rel in $relsXml.Relationships.Relationship) {
        if ($rel.Type -match "image") {
            $relMap[$rel.Id] = ($rel.Target -replace "^media/", "")
        }
    }

    $appRoot      = Split-Path (Split-Path $MyInvocation.MyCommand.Path)
    $outputDir    = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "output"
    $imagesOutDir = Join-Path $appRoot "images\tips\$ItemId"
    New-Item -ItemType Directory -Path $outputDir    -Force | Out-Null
    New-Item -ItemType Directory -Path $imagesOutDir -Force | Out-Null

    $tips       = [System.Collections.ArrayList]::new()
    $currentTip = $null
    $imgIndex   = 0

    $paragraphs = $docXml.SelectNodes("//w:body/w:p", $ns)

    foreach ($para in $paragraphs) {
        $textNodes = $para.SelectNodes(".//w:t", $ns)
        $text = (($textNodes | ForEach-Object { $_.InnerText }) -join "").Trim()
        $blips = $para.SelectNodes(".//a:blip", $ns)

        if ($blips.Count -gt 0) {
            foreach ($blip in $blips) {
                $rId = $blip.GetAttribute("embed", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
                if ($relMap.ContainsKey($rId)) {
                    $srcFile  = Join-Path $tempDir "word\media\$($relMap[$rId])"
                    $imgIndex++
                    $destName = "tip${imgIndex}.jpg"
                    $destPath = Join-Path $imagesOutDir $destName
                    Save-CompressedImage -SrcPath $srcFile -DestPath $destPath
                    if ($null -ne $currentTip) {
                        $currentTip.images.Add("images/tips/$ItemId/$destName") | Out-Null
                    }
                }
            }
        } elseif ($text -match "^## (.+)") {
            if ($null -ne $currentTip) { $tips.Add($currentTip) | Out-Null }
            $currentTip = [PSCustomObject]@{
                title  = $Matches[1].Trim()
                body   = ""
                images = [System.Collections.ArrayList]::new()
            }
        } elseif ($text -ne "" -and $null -ne $currentTip) {
            $currentTip.body = if ($currentTip.body -eq "") { $text } else { $currentTip.body + $text }
        }
    }
    if ($null -ne $currentTip) { $tips.Add($currentTip) | Out-Null }

    $result = $tips | ForEach-Object {
        $imgs = @($_.images)
        if ($imgs.Count -eq 0)     { [ordered]@{ title = $_.title; body = $_.body; image = $null } }
        elseif ($imgs.Count -eq 1) { [ordered]@{ title = $_.title; body = $_.body; image = $imgs[0] } }
        else                       { [ordered]@{ title = $_.title; body = $_.body; images = $imgs } }
    }

    $json    = ($result | ConvertTo-Json -Depth 4)
    $outFile = Join-Path $outputDir "tips_${ItemId}.json"
    $json | Out-File $outFile -Encoding utf8

    Write-Host ""
    Write-Host "=== 完了 ===" -ForegroundColor Green
    Write-Host "JSON : $outFile"
    Write-Host "画像 : $imagesOutDir ($imgIndex 枚, 幅${MaxWidth}px, 品質${Quality}%)"
    Write-Host ""
    Write-Host "equipment.json の id='$ItemId' の tips に以下を貼り付けてください:"
    Write-Host $json

} finally {
    Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
