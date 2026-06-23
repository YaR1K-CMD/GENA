Set UAC = CreateObject("Shell.Application")
UAC.ShellExecute "cmd.exe", "/c netsh advfirewall firewall add rule name=""Gennady Mobile Server"" dir=in action=allow protocol=TCP localport=8003", "", "runas", 1
