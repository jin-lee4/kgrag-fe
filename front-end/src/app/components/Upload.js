"use client";
import { useState } from "react";

const Upload = () => {
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const result = await response.json();
      const ocrResponse = await fetch("/api/ocr", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ filePath: result.filePath }),
      });

      if (ocrResponse.ok) {
        const ocrResult = await ocrResponse.json();
        setText(ocrResult.text); // Display the extracted text
      }
    } else {
      console.error("Upload failed");
    }
  };

  return (
    <div>
      {/* <input type="file" accept="application/pdf" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button> */}
      <div id="extracted-text-box">
        <div id="extracted-text">
          <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. In feugiat
            vitae leo vel aliquet. Phasellus pellentesque gravida mi in
            sagittis. Aenean ultricies suscipit urna, nec scelerisque elit
            viverra quis. Orci varius natoque penatibus et magnis dis parturient
            montes, nascetur ridiculus mus. Mauris faucibus feugiat dui ac
            viverra. Aliquam ac ipsum vestibulum, dictum magna sed, ornare
            neque. Integer interdum arcu quis egestas pretium.
          </p>
          <p>
            Nulla vitae venenatis orci, vel porta odio. Suspendisse aliquam
            facilisis dolor ac elementum. Nam dui nibh, euismod in feugiat id,
            tempus quis ex. Suspendisse maximus porttitor fermentum. Curabitur
            interdum justo nec ex consequat sodales. Nunc congue iaculis magna,
            vel vehicula neque semper sit amet. Sed semper enim sit amet
            convallis tincidunt. Morbi faucibus libero sit amet justo mollis
            lobortis. Orci varius natoque penatibus et magnis dis parturient
            montes, nascetur ridiculus mus. Nunc dignissim porta massa, quis
            sagittis odio pretium vitae. Nullam faucibus mi quis leo eleifend
            vestibulum.
          </p>
          <p>
            Nulla vitae est varius, accumsan enim quis, sollicitudin nulla.
            Maecenas a luctus augue, sed dignissim lorem. Aenean gravida metus
            at nibh varius ultrices. Quisque pulvinar nulla non gravida gravida.
            Nulla pretium sem sed venenatis lacinia. Phasellus in tincidunt
            mauris. Quisque dolor sapien, fringilla ut fermentum quis, rhoncus
            nec mi. Sed in quam vel enim pulvinar feugiat. Maecenas dignissim
            est lectus. In scelerisque libero id vehicula blandit. Nunc interdum
            tellus in metus aliquam, non suscipit nisl varius. Integer placerat
            ultrices nisi quis ultrices. In vitae orci ut sem feugiat molestie.
            Proin ultrices, tortor lacinia dapibus ultrices, augue augue blandit
            odio, ut porta lorem tellus quis sem. Sed bibendum vulputate metus
            ut tincidunt. Aenean id posuere tortor. Proin molestie placerat
            justo sed auctor. In hac habitasse platea dictumst. Class aptent
            taciti sociosqu ad litora torquent per conubia nostra, per inceptos
            himenaeos.
          </p>
      
          {/* <pre className="extracted-text">{text}</pre> */}
        </div>
      </div>
    </div>
  );
};

export default Upload;
