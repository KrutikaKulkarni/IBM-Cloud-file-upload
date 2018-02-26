from cloudant import Cloudant
from flask import Flask, render_template, request
import cf_deployment_tracker
import swiftclient.client as swiftclient
from werkzeug.utils import secure_filename
import os
import base64
import keystoneclient


# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

#Basic connections required

auth_url = ""
projectId = ""
region = "dallas"
userId = ""
password = ""

container_name = 'kruti_project'

#extension = set(['txt', 'Txt', 'pdf', 'PDF', 'PNG', 'png', 'html', 'jpg'])

UPLOAD_PATH= os.path.dirname(os.path.abspath(__file__))

#Initialise flask application
connectionst = swiftclient.Connection(
    key=password,
    authurl=auth_url,
    auth_version='3',
    os_options={"project_id": projectId,
                "user_id": userId,
                "region_name": region})

#testing connection
print "Successfully connected "
# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 5000))


@app.route('/')
def home():
    global list_of_files
    list_of_files = []

    for container in connectionst.get_account()[1]:
        for data in connectionst.get_container(container['name'])[1]:
            #list_of_files.append(format(data['name']))
            print "List of files"
    return render_template("index.html", list_of_files=connectionst.get_container(container['name'])[1])


@app.route('/download')
def home_download():
    return render_template("download.html")


@app.route('/delete')
def home_delete():
    return render_template("delete.html")




@app.route('/upload', methods=['POST', 'GET'])
def upload():
        # file to upload
        if request.form.get('add', None) == "file":
            print "OOPS"

        else:
            file = request.files['file_to_upload']
            file_name = file.filename
            file_name = secure_filename(file_name)
            file.save(os.path.join(UPLOAD_PATH, file_name))

            # get the size of the file
            file.seek(0, os.SEEK_END)
            size_of_file = file.tell()
            print size_of_file

            with open(file_name, 'rb') as sample_file:
                encrypted_file = base64.b64encode(sample_file.read())
                connectionst.put_object(container_name, file_name, contents=encrypted_file, content_type='')

            for container in connectionst.get_account()[1]:
                for data in connectionst.get_container(container['name'])[1]:
                    # list_of_files.append(format(data['name']))
                    print "List of files"
            return render_template("index.html", list_of_files=connectionst.get_container(container['name'])[1])


@app.route("/file_download", methods=['POST'])
def file_download():
    file_name = request.form['file_to_download']
    # To download file

    obj = connectionst.get_object(container_name, file_name)

    # print obj[1]
    file_content_bytes = obj[1]

    # decryption
    file_contents = base64.b64decode(file_content_bytes)
    end = str(file_contents).index('\n')
    print_message = str(file_contents)[0:end]

    with open(UPLOAD_PATH + '/Download/' + file_name, 'wb') as samp_file:
        samp_file.write(file_contents)
        print("Object %s downloaded successfully." % samp_file)
        return render_template("download.html", print_message="First line = " + print_message, list_of_files=list_of_files)


@app.route("/file_delete", methods=['POST'])
def file_delete():
    delete_file = request.form['file_to_delete']
    connectionst.delete_object(container_name, delete_file)
    return "File deleted"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
