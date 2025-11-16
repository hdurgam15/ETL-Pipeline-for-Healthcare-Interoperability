# Connect to IU VPN

You should connect to IU VPN if trying to access OpenEMR FHIR Server from your home network.

[https://servicenow.iu.edu/kb?id=kb_article_view&sysparm_article=KB0023005](https://servicenow.iu.edu/kb?id=kb_article_view&sysparm_article=KB0023005)

# Recreate the project locally

FA25_B581_Final_Project_OpenEMR_mahitha_gogu

Recreate the project using the same structure. You should know how to set up a PyCharm project by now.

This is a starter project to help get access to the patient data in OpenEMR. You have been added as a collaborator in
this repo. Do not push any changes to this repo. You can clone or copy the files and recreate the project locally.

Once you know you have access to the OpenEMR FHIR data, your project team must create another repo to collaborate
for the final submission.

Be careful: for the final project submission, you should not commit or push any sensitive data, such as an access token.
You will need to add these files to the `.gitignore file` and then collaborate with your teammates on GitHub.

# Install libraries

Run the following command in the terminal (in the project root directory):
- `pip install -r requirements.txt`
- OR 
- `pip install requests`

# Run code

There are only two files that you will need to run to get access to the patient data.

First, you will have to run the `refresh_token.py` to generate a new access_token and refresh_token. The access token
will expire every hour or so. Once it's expired, you will not have access. Therefore, you have to run the
`refresh_token.py` to get a new access_token.

Once the new access token has been generated, you can then run the `get_fhir_resource.py` code to check if the access to
the OpenEMR FHIR server works.

You can ignore all the other files. You need to copy them; however, you do not have to run them.
