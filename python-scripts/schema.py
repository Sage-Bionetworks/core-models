import synapseclient
import time  # Import the time module for sleeping between status checks
import json  # Import json to handle JSON objects

syn = synapseclient.Synapse()
syn.login()

schemaRequestBody = """
{
  "schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://repo-prod.prod.sagebase.org/repo/v1/schema/type/registered/SageCoreModels-Dataset",
    "properties": {
    "alternateName": {
      "type": "string",
      "description": "An alternative name for the dataset."
    },
    "includedInDataCatalog": {
      "type": "string",
      "description": "The data catalog that includes this dataset.",
      "default": "sagebionetworks.org"
    },
    "keywords": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Keywords or tags associated with the dataset."
    },
    "measurementTechnique": {
      "description": "The technique or technology used to measure the data.",
      "enum": [
          "2D AlamarBlue absorbance",
          "2D AlamarBlue fluorescence",
          "3D confocal imaging",
          "3D electron microscopy",
          "3D imaging",
          "3D microtissue viability",
          "actigraphy",
          "AlgometRx Nociometer",
          "auditory brainstem response",
          "ATAC-seq",
          "ATPase activity assay",
          "BrdU proliferation assay",
          "CAPP-seq",
          "CUT&RUN",
          "ChIP-seq",
          "Child Behavior Checklist for Ages 1.5-5",
          "Child Behavior Checklist for Ages 6-18",
          "CODEX",
          "confocal microscopy",
          "Corsi blocks",
          "current clamp assay",
          "distortion product otoacoustic emissions",
          "DNA optical mapping",
          "ELISA",
          "ERR bisulfite sequencing",
          "EdU proliferation assay",
          "FIA-MSMS",
          "FLIPR high-throughput cellular screening",
          "Fluorescence In Situ Hybridization",
          "Focus group",
          "FTIR spectroscopy",
          "HI-C",
          "HPLC",
          "Interview",
          "ISO-seq",
          "MIB/MS",
          "Matrigel-based tumorigenesis assay",
          "MudPIT",
          "NIH Toolbox",
          "NOMe-seq",
          "RNA array",
          "RNA-seq",
          "RPPA",
          "Riccardi and Ablon scales",
          "SNP array",
          "SUSHI",
          "Sanger sequencing",
          "Social Responsiveness Scale",
          "Social Responsiveness Scale, Second Edition",
          "T cell receptor repertoire sequencing",
          "TIDE",
          "TMT quantitation",
          "TriKinetics activity monitoring",
          "Von Frey test",
          "active avoidance learning behavior assay",
          "array",
          "atomic force microscopy",
          "autoradiography",
          "bisulfite sequencing",
          "blood chemistry measurement",
          "blue native PAGE",
          "body size trait measurement",
          "bone histomorphometry",
          "brightfield microscopy",
          "cAMP-Glo Max Assay",
          "calcium retention capacity assay",
          "cell competition",
          "cell count",
          "cell painting",
          "cell proliferation",
          "cell viability assay",
          "clinical data",
          "cNF-Skindex",
          "cognitive assessment",
          "combination library screen",
          "combination screen",
          "complex II enzyme activity assay",
          "compound screen",
          "contextual conditioning behavior assay",
          "conventional MRI",
          "Children's Dermatology Life Quality Index Questionnaire",
          "differential scanning calorimetry",
          "dynamic light scattering",
          "electrochemiluminescence",
          "electrophoretic light scattering",
          "elevated plus maze test",
          "FACE-Q Appearance-related Distress",
          "flow cytometry",
          "focus forming assay",
          "functional MRI",
          "gait measurement",
          "gel filtration chromatography",
          "gel permeation chromatography",
          "genotyping",
          "high content screen",
          "high frequency ultrasound",
          "high-performance liquid chromatography/tandem mass spectrometry",
          "immunoassay",
          "immunocytochemistry",
          "immunofluorescence",
          "immunohistochemistry",
          "in silico synthesis",
          "in vitro tumorigenesis",
          "in vivo PDX viability",
          "in vivo bioluminescence",
          "in vivo tumor growth",
          "jumping library",
          "label free mass spectrometry",
          "laser speckle imaging",
          "light scattering assay",
          "liquid chromatography-electrochemical detection",
          "liquid chromatography/mass spectrometry",
          "liquid chromatography/tandem mass spectrometry",
          "lncRNA-seq",
          "local field potential recording",
          "long term potentiation assay",
          "mRNA counts",
          "magnetic resonance spectroscopy",
          "mass spectrometry",
          "massively parallel reporter assay",
          "metabolic screening",
          "methylation array",
          "miRNA array",
          "miRNA-seq",
          "microrheology",
          "Skindex-16",
          "multi-electrode array",
          "nanoparticle tracking analysis",
          "NanoString nCounter Analysis System",
          "n-back task",
          "neuropsychological assessment",
          "next generation targeted sequencing",
          "novelty response behavior assay",
          "open field test",
          "optical tomography",
          "optical coherence tomography",
          "optokinetic reflex assay",
          "oscillatory rheology",
          "oxBS-seq",
          "oxygen consumption assay",
          "pattern electroretinogram",
          "perineurial cell thickness",
          "pharmocokinetic ADME assay",
          "phase-contrast microscopy",
          "photograph",
          "polymerase chain reaction",
          "polysomnography",
          "positron emission tomography",
          "PROMIS Cognitive Function",
          "proximity extension assay",
          "quantitative PCR",
          "questionnaire",
          "reactive oxygen species assay",
          "reporter gene assay",
          "rheometry",
          "ribo-seq",
          "rotarod performance test",
          "sandwich ELISA",
          "scCGI-seq",
          "scale",
          "SaferSeqS",
          "single molecule drug screen assay",
          "single-cell RNA-seq",
          "single cell ATAC-seq",
          "single-nucleus RNA-seq",
          "small molecule library screen",
          "sorbitol dehydrogenase activity level assay",
          "spatial frequency domain imaging",
          "spatial transcriptomics",
          "static histomorphometry",
          "static light scattering",
          "survival",
          "targeted exome sequencing",
          "traction force microscopy",
          "twin spot assay",
          "ultra high-performance liquid chromatography/tandem mass spectrometry",
          "western blot",
          "whole exome sequencing",
          "whole genome sequencing",
          "whole-cell patch clamp",
          "STR profile"
        ]
    },
    "dateModified": {
      "type": "string",
      "format": "date",
      "description": "The date on which the dataset was last modified."
    },
    "dateCreated": {
      "type": "string",
      "format": "date",
      "description": "The date on which the dataset was created."
    },
    "creator": {
      "type": "string",
      "description": "The creator of the dataset."
    },
    "funding": {
      "type": "string",
      "description": "The funding source for the dataset. Preference: Link to ROR (https://ror.org/)",
      "default": "https://ror.org/"
    },
    "isPartOf": {
      "type": "string",
      "description": "The data repository or portal to which this dataset belongs.",
      "enum": [
        "NF Data Portal",
        "AD Knowledge Portal",
        "Genie",
        "HTAN"
      ]
    },
    "conditionsOfAccess": {
      "type": "string",
      "description": "Conditions of access for the dataset."
    },
    "citation": {
      "type": "string",
      "description": "Citation details for the dataset."
    }
  }
  }
}

"""

# Issue a request to create the schema
schemaJobResponse = syn.restPOST("/schema/type/create/async/start", schemaRequestBody)

# Check on the job until it completes.
asyncJobStatus = syn.restGET(f"/asynchronous/job/{schemaJobResponse['token']}")

while asyncJobStatus["jobState"] == "PROCESSING":
    time.sleep(1)
    asyncJobStatus = syn.restGET(f"/asynchronous/job/{schemaJobResponse['token']}")

objectId = 'syn59401810' # Replace the ID with your own

jsonSchemaObjectBinding = f"""{{ "entityId": "{objectId}", "schema$id": "SageCoreModels-Dataset"}}"""

syn.restPUT(f"/entity/{objectId}/schema/binding", jsonSchemaObjectBinding)