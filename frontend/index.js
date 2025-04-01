function uploadImage() {
  const fileInput = document.getElementById("imageInput");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please select an image file.");
    return;
  }
  
  const fileName = file.name;
  const fileType = file.type;

  const customLabels = document.getElementById("CustomLabels").value || '';
  console.log("Custom Labels:", customLabels);

  getBase64(file).then((data) => {
    const apigClient = apigClientFactory.newClient();

    const body = data;
    const params = {
      filename: fileName,
      bucket: "photo-bucket-10",
      'x-amz-meta-customLabels': customLabels,
    };

    const additionalParams = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    apigClient
      .photosFilenamePut(params, body, additionalParams)
      .then(function (res) {
        if (res.status === 200 || res.status === 201) {
          console.log("Uploaded successfully");
          alert("The image was uploaded to S3!");
          console.log(res);
        } else {
          console.error("Upload failed with status:", res.status);
          alert("Failed to upload the image.");
        }
      })
      .catch((err) => {
        console.error("Upload failed:", err);
        alert("Error uploading the image.");
      });
  });
}


function getBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      let encoded = reader.result.replace(/^data:(.*;base64,)?/, '');
      if (encoded.length % 4 > 0) {
        encoded += '='.repeat(4 - (encoded.length % 4));
      }
      resolve(encoded);
    };
    reader.onerror = (error) => reject(error);
  });
}



function searchText() {
  var searchTerm = document.getElementById("searchText").value.trim();
  console.log("Search Term:", searchTerm);

  if (!searchTerm) {
    alert("Please enter a search query.");
    return;
  }

  var apigClient = apigClientFactory.newClient();

  var params = {
    q: searchTerm,
  };

  var body = null;

  var additionalParams = {
  };

  apigClient
    .searchGet(params, body, additionalParams)
    .then(function (res) {
      console.log("Search success");
      console.log("Response data:", res.data);
	  
      showImages(res.data);
    })
    .catch(function (err) {
      console.error("Search Failed:", err);
      alert("Error searching for photos.");
    });
}

function showImages(images) {
  const searchResultDiv = document.getElementById("searchResult");
  searchResultDiv.innerHTML = "";
  console.log("Displaying Images");

  if (images.length === 0) {
    searchResultDiv.innerHTML = "No images found.";
  } else {
    images.forEach((item) => {
      const objectKey = item.objectKey;
      const bucketName = item.bucket;

      
      const imageUrl = `https://${bucketName}.s3.amazonaws.com/${encodeURIComponent(objectKey)}`;

      const img = document.createElement("img");
      img.src = imageUrl;
      img.alt = objectKey;
      img.style.width = "200px";
      img.style.margin = "5px";
      searchResultDiv.appendChild(img);
    });
  }
}

