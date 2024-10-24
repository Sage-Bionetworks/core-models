const fs = require('fs').promises;
const path = require('path');

// Function to load and parse the JSON-LD file from the local filesystem
async function loadDataModel(filePath) {
  try {
    const absolutePath = path.resolve(filePath); // Convert relative path to absolute path
    const data = await fs.readFile(absolutePath, 'utf8'); // Read the file as a string
    const dataModel = JSON.parse(data); // Parse the file as JSON
    return dataModel;
  } catch (error) {
    console.error("Error loading JSON-LD file:", error);
  }
}

// Helper function to get project categories
function getProjectCategories(graph) {
  const projectCategory = graph.find(item => item["@id"] === "projectCategory");
  return projectCategory.rangeIncludes.map(project => {
    const projectDetails = graph.find(p => p["@id"] === project["@id"]);
    return {
      id: project["@id"],
      name: projectDetails ? projectDetails.displayName : project["@id"]
    };
  });
}

// Helper function to get activities and their dependencies
function getActivityDependencies(activity, graph) {
  const activityDetails = graph.find(item => item["@id"] === activity["@id"]);
  if (!activityDetails || !activityDetails.requiresDependency) return [];
  
  return activityDetails.requiresDependency.map(dep => {
    const depDetails = graph.find(d => d["@id"] === dep["@id"]);
    return {
      id: dep["@id"],
      name: depDetails ? depDetails.displayName : dep["@id"],
      roles: getRequiredRoles(dep["@id"], graph)
    };
  });
}

// Helper function to get required roles for each activity enum
function getRequiredRoles(enumId, graph) {
  const enumDetails = graph.find(item => item["@id"] === enumId);
  if (!enumDetails || !enumDetails.requiresDependency) return [];

  return enumDetails.requiresDependency.map(role => {
    const roleDetails = graph.find(r => r["@id"] === role["@id"]);
    return {
      id: role["@id"],
      name: roleDetails ? roleDetails.displayName : role["@id"],
      effort: ["sz1", "sz2", "sz3", "sz4", "sz5"] // Example effort sizes
    };
  });
}

// Generate the form schema
function generateFormSchema(dataModel) {
  const graph = dataModel["@graph"];
  
  const projectCategories = getProjectCategories(graph);
  const activities = graph.filter(item => item["@id"] === "activity")[0].rangeIncludes.map(activity => {
    const activityDetails = graph.find(act => act["@id"] === activity["@id"]);
    return {
      id: activity["@id"],
      name: activityDetails ? activityDetails.displayName : activity["@id"],
      enums: getActivityDependencies(activity, graph)
    };
  });

  const formSchema = {
    title: "Project and Activities Form",
    type: "object",
    properties: {
      projectCategory: {
        type: "string",
        title: "What is the project?",
        enum: projectCategories.map(p => p.id),
        enumNames: projectCategories.map(p => p.name)
      },
      activities: {
        type: "object",
        properties: {}
      }
    },
    required: ["projectCategory", "activities"]
  };

  // Adding activities and dependencies
  activities.forEach(activity => {
    const enums = activity.enums.reduce((acc, activityEnum) => {
      acc[activityEnum.id] = {
        type: "string",
        title: activityEnum.name,
        dependencies: {}
      };
      if (activityEnum.roles.length > 0) {
        const roleDependencies = {};
        activityEnum.roles.forEach(role => {
          roleDependencies[role.id] = {
            type: "string",
            title: `${role.name} effort`,
            enum: role.effort,
            enumNames: ["extra small", "small", "medium", "large", "extra large"]
          };
        });
        acc[activityEnum.id].dependencies = { roles: roleDependencies };
      }
      return acc;
    }, {});

    formSchema.properties.activities.properties[activity.id] = {
      type: "string",
      title: `What ${activity.name} activities are needed?`,
      enum: activity.enums.map(e => e.id),
      enumNames: activity.enums.map(e => e.name),
      dependencies: enums
    };
  });

  return formSchema;
}

// Save the generated JSON schema to a file with the current date and time
async function saveFormSchemaToFile(schema) {
  const now = new Date();
  const timestamp = now.toISOString().replace(/[-:.]/g, "_"); // Format date for filename
  const filename = `form_schema_${timestamp}.json`;
  const filePath = path.join(__dirname, filename); // Save in the current directory

  try {
    await fs.writeFile(filePath, JSON.stringify(schema, null, 2), 'utf8');
    console.log(`Form schema saved as: ${filename}`);
  } catch (error) {
    console.error("Error saving form schema to file:", error);
  }
}

// Load the data model from a local JSON-LD file and generate the form schema
const jsonLdFilePath = './genericform.jsonld'; // Replace with the relative path to your allocation.jsonld file

loadDataModel(jsonLdFilePath).then(dataModel => {
  if (dataModel) {
    const formSchema = generateFormSchema(dataModel);
    saveFormSchemaToFile(formSchema); // Save the generated form schema to a file
  }
});
