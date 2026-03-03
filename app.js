document.addEventListener("DOMContentLoaded", () => {

  const detectBtn = document.getElementById("detectBtn");
  const sidebar = document.getElementById("sidebar");
  const startBtn = document.getElementById("startBtn");
  const statusText = document.getElementById("status");

  const geojsonOutput = document.getElementById("geojsonOutput");
  const geojsonContent = document.getElementById("geojsonContent");

  // ---------- SIDEBAR TOGGLE ----------
  if (detectBtn && sidebar) {
    detectBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }

  // ---------- START DETECTION ----------
  if (startBtn) {
    startBtn.addEventListener("click", async () => {

      const kmlInput = document.getElementById("kmlFile");
      const fromDateInput = document.getElementById("fromDate");
      const toDateInput = document.getElementById("toDate");

      const kmlFile = kmlInput?.files[0];
      const fromDate = fromDateInput?.value;
      const toDate = toDateInput?.value;

      if (!kmlFile || !fromDate || !toDate) {
        statusText.classList.remove("hidden");
        statusText.innerText = "Please upload KML and select dates.";
        return;
      }

      startBtn.disabled = true;
      startBtn.classList.add("running");
      statusText.classList.remove("hidden");
      statusText.innerText = "🟢 Initializing change detection...";

      const formData = new FormData();
      formData.append("kml", kmlFile);
      formData.append("from_date", fromDate);
      formData.append("to_date", toDate);

      try {
        const response = await fetch("/start", {
          method: "POST",
          body: formData
        });

        if (!response.ok) {
          throw new Error("Pipeline already running");
        }

        listenToStatus();   // 🔥 KEEP SSE AS-IS

      } catch (error) {
        console.error(error);
        statusText.innerText = "❌ Detection already running.";
        startBtn.disabled = false;
        startBtn.classList.remove("running");
      }
    });
  }

  // ---------- STATUS STREAM (SSE) ----------
  function listenToStatus() {
    const eventSource = new EventSource("/status-stream");

    eventSource.onmessage = async (event) => {
      statusText.innerText = event.data;

      const msg = event.data.toLowerCase();

      // ✅ FLEXIBLE completion detection (CRITICAL FIX)
      if (
        msg.includes("completed") ||
        msg.includes("error") ||
        msg.includes("failed")
      ) {
        eventSource.close();
        await fetchResult();

        startBtn.disabled = false;
        startBtn.classList.remove("running");
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      statusText.innerText = "❌ Status stream disconnected.";
      startBtn.disabled = false;
      startBtn.classList.remove("running");
    };
  }

  // ---------- FETCH FINAL RESULT ----------
  async function fetchResult() {
    try {
      const response = await fetch("/result");
      const geojson = await response.json();

      if (geojson && geojson.features) {
        geojsonOutput.classList.remove("hidden");
        geojsonContent.textContent = JSON.stringify(geojson, null, 2);
      } else {
        statusText.innerText = "⚠️ No change detected.";
      }

    } catch (err) {
      console.error(err);
      statusText.innerText = "❌ Failed to fetch result.";
    }
  }

});
