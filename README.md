# SpisMed-Backup
Tager en backup af dit kollegiekøkkens økonomi-status på SpisMed.nu og gemmer som txt-fil.
Sæt evt. et cronjob op til at køre det dagligt.

## Usage: 
```
backup_spismed [OPTIONS]
Options:
    -h           Print this help message
    -p           Print the standings without saving to a file
    -l           List the current backups
    -c           Clean the backups directory leaving only the 10 latest backups
    -d "DST"     Saves the backup in the supplied destination
    --configure  Runs the configuration wiz
```
