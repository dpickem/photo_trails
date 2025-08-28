const { useState, useRef } = React;

function Uploader() {
  const [message, setMessage] = useState(null);
  const [log, setLog] = useState([]);
  const fileRef = useRef(null);
  const dirRef = useRef(null);

  const upload = async (inputRef) => {
    const files = inputRef.current.files;
    if (!files || files.length === 0) {
      setMessage("No file selected.");
      setLog([]);
      return;
    }
    const formData = new FormData();
    for (const file of files) {
      formData.append("photos", file, file.name);
    }
    try {
      const resp = await fetch("/upload", { method: "POST", body: formData });
      const data = await resp.json();
      setMessage(data.message);
      setLog(data.log);
    } catch (err) {
      setMessage("Upload failed.");
      setLog([String(err)]);
    }
    inputRef.current.value = "";
  };

  return React.createElement(
    "div",
    { id: "upload-panel" },
    React.createElement(
      "div",
      null,
      React.createElement("input", { ref: fileRef, type: "file", accept: "image/*", multiple: true }),
      React.createElement(
        "button",
        { onClick: () => upload(fileRef) },
        "Upload Files"
      )
    ),
    React.createElement(
      "div",
      null,
      React.createElement("input", {
        ref: dirRef,
        type: "file",
        accept: "image/*",
        multiple: true,
        webkitdirectory: "",
        directory: "",
      }),
      React.createElement(
        "button",
        { onClick: () => upload(dirRef) },
        "Upload Directory"
      )
    ),
    message
      ? React.createElement("div", { className: "status-box" }, message)
      : null,
    log.length > 0
      ? React.createElement("pre", { id: "debug-console" }, log.join("\n"))
      : null
  );
}

ReactDOM.createRoot(document.getElementById("uploader-root")).render(
  React.createElement(Uploader)
);
