param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("Tables", "Views", "Procedures", "Query")]
    [string]$Action,
    [string]$SQLQuery = ""
)

$pass = 'T3CN0L0G14@24'
$connString = "Server=192.168.1.85,1433;Database=RUSTON_PRODUCAO;User Id=Tecnologia;Password=$pass;Encrypt=False;TrustServerCertificate=True;"

$queries = @{
    "Tables"     = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
    "Views"      = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS ORDER BY TABLE_NAME"
    "Procedures" = "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE = 'PROCEDURE' ORDER BY ROUTINE_NAME"
}

$finalQuery = if ($Action -eq "Query") { $SQLQuery } else { $queries[$Action] }

try {
    $connection = New-Object System.Data.SqlClient.SqlConnection($connString)
    $command = New-Object System.Data.SqlClient.SqlCommand($finalQuery, $connection)
    $connection.Open()
    $adapter = New-Object System.Data.SqlClient.SqlDataAdapter($command)
    $dataset = New-Object System.Data.DataSet
    $adapter.Fill($dataset) > $null
    $dataset.Tables[0] | Format-Table -AutoSize
    $connection.Close()
}
catch {
    Write-Error "Erro: $_"
}