const { useState, useRef, useEffect } = React;

function Uploader() {
  const [message, setMessage] = useState(null);
  const [log, setLog] = useState([]);
  const [count, setCount] = useState(0);
  const fileRef = useRef(null);
  const dirRef = useRef(null);

  const fetchCount = async () => {
    try {
      const resp = await fetch("/photos");
      const data = await resp.json();
      setCount(data.length);
    } catch (err) {
      setCount(0);
    }
  };

  useEffect(() => {
    fetchCount();
  }, []);

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
    fetchCount();
  };

  return React.createElement(
    "div",
    { id: "upload-panel" },
    React.createElement(
      "details",
      { open: true },
      React.createElement("summary", null, "Upload Files"),
      React.createElement(
        "div",
        { className: "field" },
        React.createElement("input", { ref: fileRef, type: "file", accept: "image/*", multiple: true }),
        React.createElement(
          "button",
          { onClick: () => upload(fileRef) },
          "Upload"
        )
      )
    ),
    React.createElement(
      "details",
      null,
      React.createElement("summary", null, "Upload Directory"),
      React.createElement(
        "div",
        { className: "field" },
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
          "Upload"
        )
      )
    ),
    React.createElement(
      "details",
      { open: true },
      React.createElement("summary", null, "Status"),
      message
        ? React.createElement("div", { className: "status-box" }, message)
        : null,
      log.length > 0
        ? React.createElement("pre", { id: "debug-console" }, log.join("\n"))
        : null,
      React.createElement(
        "div",
        { className: "status-box" },
        `Database rows: ${count}`
      )
    ),
    React.createElement(
      "details",
      null,
      React.createElement("summary", null, "Database"),
      React.createElement(
        "form",
        { action: "/clear-db", method: "post" },
        React.createElement(
          "button",
          { type: "submit" },
          "Clear Database"
        )
      )
    )
  );
}

ReactDOM.createRoot(document.getElementById("uploader-root")).render(
  React.createElement(Uploader)
);
