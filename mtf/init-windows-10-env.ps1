function Test-IsAdministrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdministrator)) {
    Write-Host "run this ps1 with priv" -ForegroundColor Red
    exit
}

$pathsToAdd = @(
    "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps",
    "d:\lang\python\Scripts",
    "d:\lang\python"
)

$systemPathsToAdd = @(
    "%SystemRoot%\system32",
    "%SystemRoot%",
    "%SystemRoot%\System32\Wbem",
    "%SYSTEMROOT%\System32\WindowsPowerShell\v1.0",
    "%SYSTEMROOT%\System32\OpenSSH",
    "c:\Program Files\NVIDIA Corporation\NVIDIA NvDLISR",
    "c:\Program Files (x86)\NVIDIA Corporation\PhysX\Common",
    "c:\Program Files\dotnet",
    "d:\lang\java\java-microsoft-jdk-21.0.2\bin",
    "d:\bin\git\bin"
    "d:\software\bandizip",
    "d:\sec\xftp",
    "d:\sec\xshell"
)

# CLASSPATH and JAVA_HOME for system variables
$systemVars = @{
    "CLASSPATH" = ".;%JAVA_HOME%\lib\dt.jar;%JAVA_HOME%\lib\tools.jar";
    "JAVA_HOME" = "d:\lang\java\java-microsoft-jdk-21.0.2";
}

function Add-EnvironmentVariable {
    param (
        [string]$VariableName,
        [string]$Path,
        [ValidateSet("User", "Machine")] 
        [string]$Scope = "User"
    )
    
    $currentPath = [System.Environment]::GetEnvironmentVariable($VariableName, [System.EnvironmentVariableTarget]::$Scope)
    if ($currentPath -notlike "*$Path*") {
        $newPath = $currentPath + ";" + $Path
        [System.Environment]::SetEnvironmentVariable($VariableName, $newPath, [System.EnvironmentVariableTarget]::$Scope)
        Write-Output "$VariableName path added: $Path"
    } else {
        Write-Output "$VariableName path already existed: $Path"
    }
}

# Add User Path Variables
foreach ($path in $pathsToAdd) {
    Add-EnvironmentVariable -VariableName "PATH" -Path $path -Scope "User"
}

# Add System Path Variables
foreach ($path in $systemPathsToAdd) {
    Add-EnvironmentVariable -VariableName "PATH" -Path $path -Scope "Machine"
}

# Add\Update System Variables
foreach ($var in $systemVars.GetEnumerator()) {
    $currentValue = [System.Environment]::GetEnvironmentVariable($var.Key, [System.EnvironmentVariableTarget]::Machine)
    if ($currentValue -ne $var.Value) {
        [System.Environment]::SetEnvironmentVariable($var.Key, $var.Value, [System.EnvironmentVariableTarget]::Machine)
        Write-Output "$($var.Key) set to: $($var.Value)"
    } else {
        Write-Output "$($var.Key) already set to the correct value"
    }
}
