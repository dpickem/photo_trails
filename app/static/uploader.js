const { useState, useRef, useEffect } = React;

function SidebarHeader({ count }) {
  return React.createElement(
    "div",
    { className: "sidebar-header" },
    React.createElement(
      "div",
      { className: "app-title" },
      React.createElement("span", null, "📸"),
      React.createElement("span", null, "Photo Trails")
    ),
    React.createElement("span", { className: "pill" }, `${count} photos`)
  );
}

function Progress({ value }) {
  return React.createElement(
    "div",
    { className: "progress" },
    React.createElement("div", { className: "progress-bar", style: { width: `${value}%` } })
  );
}

function PhotosTable({ photos }) {
  const headers = ["id", "file", "latitude", "longitude"];
  const rows = photos.map((p) => ({
    id: p.id,
    file: p.file_path ? p.file_path.split("/").pop() : "",
    latitude: p.latitude ?? "",
    longitude: p.longitude ?? "",
    url: p.url,
  }));
  return React.createElement(
    "div",
    { className: "table-container" },
    React.createElement(
      "table",
      { className: "data-table" },
      React.createElement(
        "thead",
        null,
        React.createElement(
          "tr",
          null,
          headers.map((h) => React.createElement("th", { key: h }, h))
        )
      ),
      React.createElement(
        "tbody",
        null,
        rows.map((r) =>
          React.createElement(
            "tr",
            { key: r.id },
            React.createElement("td", null, r.id),
            React.createElement(
              "td",
              null,
              r.url
                ? React.createElement("a", { href: r.url, target: "_blank" }, r.file)
                : r.file
            ),
            React.createElement("td", null, String(r.latitude)),
            React.createElement("td", null, String(r.longitude))
          )
        )
      )
    )
  );
}

function Uploader() {
  const [message, setMessage] = useState(null);
  const [log, setLog] = useState([]);
  const [count, setCount] = useState(0);
  const [photos, setPhotos] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileRef = useRef(null);
  const dirRef = useRef(null);

  // Heuristics for batching to avoid overloading the server.
  // Batches are limited by both total bytes and max file count.
  const MAX_BATCH_BYTES = (window.APP_CONFIG && window.APP_CONFIG.maxBatchBytes) || 40 * 1024 * 1024; // 40MB
  const MAX_FILES_PER_BATCH = (window.APP_CONFIG && window.APP_CONFIG.maxFilesPerBatch) || 16;

  const makeBatches = (files) => {
    const batches = [];
    let current = [];
    let currentBytes = 0;
    for (const f of files) {
      const size = f.size || 0;
      const wouldExceedBytes = currentBytes + size > MAX_BATCH_BYTES;
      const wouldExceedCount = current.length + 1 > MAX_FILES_PER_BATCH;
      if (current.length > 0 && (wouldExceedBytes || wouldExceedCount)) {
        batches.push(current);
        current = [];
        currentBytes = 0;
      }
      current.push(f);
      currentBytes += size;
    }
    if (current.length) batches.push(current);
    return batches;
  };

  const fetchPhotos = async () => {
    try {
      const resp = await fetch("/photos");
      const data = await resp.json();
      setPhotos(Array.isArray(data) ? data : []);
      setCount(Array.isArray(data) ? data.length : 0);
    } catch (err) {
      setPhotos([]);
      setCount(0);
    }
  };

  useEffect(() => {
    fetchPhotos();
    const onDebug = (e) => setLog((prev) => [...prev, String(e.detail)]);
    window.addEventListener("debug-log", onDebug);
    if (!window.debugLog) {
      window.debugLog = (msg) => {
        window.dispatchEvent(new CustomEvent("debug-log", { detail: msg }));
      };
    }
    return () => window.removeEventListener("debug-log", onDebug);
  }, []);

  const uploadWithProgress = (formData, onProgress) =>
    new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/upload");
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          if (onProgress) onProgress(e.loaded, e.total);
        }
      };
      xhr.onreadystatechange = () => {
        if (xhr.readyState === 4) {
          try {
            const json = JSON.parse(xhr.responseText || "{}");
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(json);
            } else {
              reject(json);
            }
          } catch (e) {
            reject({ message: "Invalid server response" });
          }
        }
      };
      xhr.onerror = () => reject({ message: "Network error" });
      xhr.send(formData);
    });

  const handleUpload = async (inputRef) => {
    const files = inputRef.current.files;
    if (!files || files.length === 0) {
      setMessage("No file selected.");
      setLog([]);
      return;
    }
    const fileArray = Array.from(files);
    const totalBytes = fileArray.reduce((acc, f) => acc + (f.size || 0), 0) || 1;
    const batches = makeBatches(fileArray);
    window.debugLog && window.debugLog(`Batching ${fileArray.length} files into ${batches.length} batch(es). Limits: ${MAX_FILES_PER_BATCH} files or ${(MAX_BATCH_BYTES / 1024 / 1024).toFixed(0)}MB per batch.`);
    let uploadedBytes = 0;
    let combinedLog = [];
    let totalSuccess = 0;
    try {
      setIsUploading(true);
      setProgress(0);
      let processed = 0;
      for (let b = 0; b < batches.length; b++) {
        const batch = batches[b];
        const formData = new FormData();
        let batchBytes = 0;
        for (const file of batch) {
          formData.append("photos", file, file.name);
          batchBytes += file.size || 0;
        }
        const data = await uploadWithProgress(formData, (loaded) => {
          const totalLoaded = uploadedBytes + loaded;
          const pct = Math.min(100, Math.round((totalLoaded / totalBytes) * 100));
          setProgress(pct);
        });
        if (Array.isArray(data.log)) combinedLog = combinedLog.concat(data.log);
        // success count is embedded in message like "X of Y photo(s) ingested."
        const m = (data.message || "").match(/^(\d+)/);
        if (m) totalSuccess += parseInt(m[1], 10) || 0;
        uploadedBytes += batchBytes;
        processed += batch.length;
        setMessage(`Processed batch ${b + 1}/${batches.length} (${processed}/${fileArray.length} files)`);
        setLog((prev) => prev.concat(data.log || []));
        await fetchPhotos();
        window.dispatchEvent(new Event('photos-updated'));
      }
      setMessage(`${totalSuccess} of ${fileArray.length} file(s) ingested.`);
      window.dispatchEvent(new Event('photos-updated'));
    } catch (err) {
      setMessage(err && err.message ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
      setTimeout(() => setProgress(0), 800);
    }
    inputRef.current.value = "";
    fetchPhotos();
  };

  const clearDb = async () => {
    const url = (window.APP_CONFIG && window.APP_CONFIG.clearDbUrl) || "/clear";
    try {
      const resp = await fetch(url, { method: "POST" });
      if (!resp.ok) throw new Error("Failed to clear database");
      setMessage("Database cleared");
      fetchPhotos();
    } catch (e) {
      setMessage("Unable to clear database");
    }
  };

  return React.createElement(
    "div",
    { id: "upload-panel" },
    React.createElement(SidebarHeader, { count }),
    React.createElement(
      "div",
      { className: "upload-card" },
      React.createElement("div", { className: "muted" }, "Upload files or a folder"),
      React.createElement(
        "div",
        { className: "input-row" },
        React.createElement("input", { ref: fileRef, type: "file", accept: "image/*,video/*", multiple: true }),
        React.createElement(
          "button",
          { className: "primary", onClick: () => handleUpload(fileRef), disabled: isUploading },
          isUploading ? "Uploading..." : "Upload Files"
        )
      ),
      // Directory upload removed; use multi-select instead
      React.createElement(Progress, { value: progress })
    ),
    message ? React.createElement("div", { className: "status-box" }, message) : null,
    React.createElement(
      "div",
      { className: "status-box" },
      React.createElement("div", { className: "muted" }, "Database preview"),
      React.createElement(PhotosTable, { photos })
    ),
    React.createElement(
      "div",
      { className: "status-box" },
      React.createElement(
        "div",
        { className: "input-row" },
        React.createElement("div", { className: "muted" }, "Debug output"),
        React.createElement(
          "button",
          { onClick: () => setLog([]) },
          "Clear"
        )
      ),
      React.createElement("pre", { id: "debug-console" }, log.join("\n"))
    ),
    React.createElement(
      "div",
      { className: "input-row" },
      React.createElement(
        "button",
        { onClick: clearDb },
        "Clear Database"
      )
    )
  );
}

ReactDOM.createRoot(document.getElementById("uploader-root")).render(
  React.createElement(Uploader)
);
