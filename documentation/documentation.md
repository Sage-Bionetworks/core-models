## Documentation 

### Logging In to go.coremodels.io

1. Open your web browser and go to [go.coremodels.io](https://go.coremodels.io).
2. Click on **Login with Google**.
3. Enter your SageBase email and password:
   - **Username:** Your SageBase email address.
   - **Password:** Your SageBase password.
4. Click **Log In** to access the platform.

### Request Access to the “Sage Template - Make a Copy Only” Project

5. Ask Christina to add you to the **“Sage Template - Make a Copy Only”** project.
6. Once added, click **Duplicate** to create your own copy of the Sage Template.

### [Video 1: Making a New Project and Importing Data Model](https://scribehow.com/shared/Core_Models_Part_1_Making_a_new_project__WzmIsAptQQaYJGG8L9AYTw)

### Getting Started with Your Project

7. Navigate to **Grids -> JSON-LD Import/Export Config Grids** where you will find the **SAGE CONFIG TEMPLATE**.

8. **Rename the Project:**
   - Click the three dots in the upper-right corner (`...`) and select **Settings**.
   - Change the **Title** to reflect the relevant project name.

9. **Rename a Space:**
   - Go to **Taxonomies -> Spaces Definitions**.

10. **Create a New Space:**
    - Click on **All Spaces** or the current space name in the upper-left corner.
    - Select **+Add** to create a new space.
    - To add multiple spaces at once, click **Add More**. If adding just one space, click **Add & Close**.

11. **Configure Plugins:**
    - Click the three dots in the upper-right corner (`...`) and select **Plugins**.
    - Under **JSON-LD Importer**, click **Open**.

12. **Importing a JSON-LD File:**
    - By default, the import name is set to the date and time (e.g., "Import - 6/12/2024, 10:16:36 PM"). It's recommended to keep this name for easier backup restoration.
    - For **Schema URL**, you can either:
      - Enter a link to the JSON-LD file (such as a raw data link from GitHub), or
      - Click **Click to Upload** and select the `.jsonld` file from your local computer.
    - Under **In Space**, make sure to select the correct space where the data model should be uploaded.
    - For **Import Type**:
      - If this is your first import, select **Dynamic**.
      - For subsequent imports or updates, select **Merge** to avoid creating duplicate nodes.
    - Under **Import Profile**, choose **SAGE CONFIG TEMPLATE**. This template converts the data to a format compatible with the schematic tool.

13. **Proceeding with the Import:**
    - Click **Next** to preview the import, which will display the transformations based on the SAGE CONFIG TEMPLATE. Typically, no changes are needed here.
    - Click the green box labeled **Proceed** in the upper left to continue.

14. **Monitoring the Import Process:**
    - A "Task Details" menu will appear, showing the progress through steps like "Initializing," "Parsing the file," "Generating the schema," and "Creating nodes and relations." If everything is successful, the status will show **Success**.

15. **View Your Types:**
    - Refresh the page and go to **Types -> Types Grid** to see all your types within the selected space.
    - If the types don't appear, double-check that you're in the correct space by selecting it from the drop-down menu in the upper-left corner.

### Sharing Your Project

16. Sharing settings are configured on a 'project by project basis'. To add contributors, select the upper right three dots (`...`) and click **Contributors**. Next to **Add Contributor**, type in the user's email. Select the role you want the user to have (Admin, Viewer, Editor, Exporter) and click the green button **Add**.

### Common Errors 

17. Not having the "label" column filled out will result in the schema convert function not working.

18. Not having "bts:" results in an error for schema convert.

### Tips

19. [Add your tips here if applicable]
