# What is Core Models

# Schematic Setup and Usage Instructions

## Setup


1. **Create and activate a new conda environment:** (not sure if this step is needed)
   ```bash
   conda create -n 'schematicpy' python=3.10
   conda init bash
   conda activate schematicpy
   ```

2. **Install schematicpy:**
   ```bash
   pip install schematicpy
   ```

3. **Download the configuration file:**
   ```bash
   wget https://raw.githubusercontent.com/Sage-Bionetworks/schematic/main/config_example.yml
   ```
 - make changes to the configuration file - this only has to be done once 
4. **Short term fix for version issue:**
   ```bash
   pip3 install ipython==8.18.1
   ```

## Using Schematic

### Start Schematic
```bash
schematic
```

### Make the Schematic Service Account Credential File
```bash
echo $SCHEMATIC_SERVICE_ACCT_CREDS | base64 -d > creds.json
```

### Test Creating a Google Sheet
```bash
schematic manifest -c config.yml get -t 'test' -s
```

### Convert JSON-LD to JSON-LD with Schematic Friendly Formatting
```bash
schematic schema convert DUO-terms.jsonld
```

### Generate a Google Sheet Manifest
```bash
schematic manifest -c config.yml get -t 'test' -s -dt DUOTemplate
```

---

These instructions provide a step-by-step guide to setting up and using the Schematic tool for managing data and schemas.
