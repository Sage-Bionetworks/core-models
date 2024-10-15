# What is Core-Models Repository

This repository hosts data models sourced from various projects within Sage. All data models included here must be publicly accessible.

These data models are generated using the CoreModels software (coremodels.io). This platform enables users to interact with data models visually, facilitating their creation and management. Once created, the data models are exported as .jsonld files, such as DUO-terms.jsonld, and pushed to this GitHub repository.

Future development efforts will focus on expanding the generation of core models across Sage in a jsonld format. This will enhance the interoperability and accessibility of data models within the organization.

# Schematic Setup and Usage Instructions

These instructions provide a step-by-step guide to setting up and using the Schematic tool for managing data and schemas.

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

### Each time you run codespace: Make the Schematic Service Account Credential File
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

### To generate manifest:
Change location inside config.yml to the jsonld you want to create the template from. 
```yaml
  # Location of your schema jsonld, it must be a path relative to this file or absolute
  location: "DUO-terms.jsonld"

```

### Generate a Google Sheet Manifest
```bash
schematic manifest -c config.yml get -t 'test' -s -dt DUOTemplate
schematic manifest -c config.yml get -t 'ProjectAllocationTable' -s -dt ProjectAllocationTable

```

### Generate a Google Sheet Manifest for Project Allocation
```bash
schematic manifest -c config.yml get -t 'ProjectAllocationTable' -s -dt ProjectAllocationTable
schematic manifest -c config.yml get -t 'FunctionTable' -s -dt FunctionTable
schematic manifest -c config.yml get -t 'ProductOrServiceTable' -s -dt ProductOrServiceTable
schematic manifest -c config.yml get -t 'SizeTable' -s -dt SizeTable
schematic manifest -c config.yml get -t 'ActivityTable' -s -dt ActivityTable


```
---
### examples for challenges
```bash
schematic manifest -c config.yml get -t 'ChallengePlatform' -s -dt ChallengePlatform -o '/workspaces/core-models/challenges-manifests/ChallengePlatform.csv'
schematic manifest -c config.yml get -t 'ChallengeSubmissionType' -s -dt ChallengeSubmissionType -o '/workspaces/core-models/challenges-manifests/ChallengeSubmissionType.csv'
schematic manifest -c config.yml get -t 'ChallengeIncentive' -s -dt ChallengeIncentive -o '/workspaces/core-models/challenges-manifests/ChallengeIncentive.csv'
schematic manifest -c config.yml get -t 'ChallengeCategory' -s -dt ChallengeCategory -o '/workspaces/core-models/challenges-manifests/ChallengeCategory.csv'
schematic manifest -c config.yml get -t 'ChallengeContribution' -s -dt ChallengeContribution -o '/workspaces/core-models/challenges-manifests/ChallengeContribution.csv'
schematic manifest -c config.yml get -t 'Challenge' -s -dt Challenge -o '/workspaces/core-models/challenges-manifests/Challenge.csv'
schematic manifest -c config.yml get -t 'ChallengeInputDataType' -s -dt ChallengeInputDataType -o '/workspaces/core-models/challenges-manifests/ChallengeInputDataType.csv'
schematic manifest -c config.yml get -t 'EdamConcept' -s -dt EdamConcept -o '/workspaces/core-models/challenges-manifests/EdamConcept.csv'
```


---
### to run csv to json converter 

```bash
python importcsv.py
```
# make sure the directory is correct.  If running in CodeSpace, make sure the directory is relative to your github environment (for example /workspaces/core-models/)

