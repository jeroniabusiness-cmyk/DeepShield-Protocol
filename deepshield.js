class DeepShield {
    constructor() {
        this.stream = null;
        this.mediaRecorder = null;
        this.recordedChunks = [];
    }

    async startChallenge(apiUrl) {
        let overlay = null;
        let styleSheet = null;

        try {
            // 1. Access Webcam
            this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });

            // Create Overlay
            overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.zIndex = '9999';
            overlay.style.backgroundColor = 'black'; // Start black
            overlay.style.display = 'flex';
            overlay.style.flexDirection = 'column';
            overlay.style.justifyContent = 'center';
            overlay.style.alignItems = 'center';
            overlay.style.color = 'white';
            overlay.style.fontFamily = "'Inter', sans-serif";

            // Create Text Container
            const textContainer = document.createElement('h2');
            textContainer.innerText = "Prepare for Liveness Check...";
            textContainer.style.marginBottom = "20px";
            textContainer.style.fontSize = "24px";
            textContainer.style.fontWeight = "600";
            textContainer.style.textShadow = "0 2px 4px rgba(0,0,0,0.5)";
            overlay.appendChild(textContainer);

            // Preview Video Container (Visible during check)
            const videoContainer = document.createElement('div');
            videoContainer.style.position = 'relative';
            videoContainer.style.width = '320px';
            videoContainer.style.height = '240px';
            videoContainer.style.borderRadius = '12px';
            videoContainer.style.overflow = 'hidden';
            videoContainer.style.border = '2px solid rgba(255,255,255,0.2)';
            videoContainer.style.boxShadow = '0 0 20px rgba(0,0,0,0.5)';
            videoContainer.style.background = '#000';

            // Preview Video Element
            const videoElement = document.createElement('video');
            videoElement.style.width = '100%';
            videoElement.style.height = '100%';
            videoElement.style.objectFit = 'cover';
            videoElement.style.transform = 'scaleX(-1)'; // Mirror effect
            videoElement.srcObject = this.stream;
            videoElement.play();

            // Scanning Line Animation
            const scanLine = document.createElement('div');
            scanLine.style.position = 'absolute';
            scanLine.style.top = '0';
            scanLine.style.left = '0';
            scanLine.style.width = '100%';
            scanLine.style.height = '2px';
            scanLine.style.background = '#00f3ff';
            scanLine.style.boxShadow = '0 0 10px #00f3ff';
            scanLine.style.animation = 'scan 1.5s linear infinite';

            // Add keyframes for scan if not present (inline style hack for JS-only)
            styleSheet = document.createElement("style");
            styleSheet.innerText = `
                @keyframes scan {
                    0% { top: 0%; opacity: 0; }
                    10% { opacity: 1; }
                    90% { opacity: 1; }
                    100% { top: 100%; opacity: 0; }
                }
            `;
            document.head.appendChild(styleSheet);

            videoContainer.appendChild(videoElement);
            videoContainer.appendChild(scanLine);
            overlay.appendChild(videoContainer);

            document.body.appendChild(overlay);

            // 2. Strategy: Deterministic Challenge
            const sequence = ['red', 'green', 'blue'];

            // 3. Start Recording
            this.recordedChunks = [];
            this.mediaRecorder = new MediaRecorder(this.stream, { mimeType: 'video/webm' });

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };

            const recordStartTime = performance.now();
            this.mediaRecorder.start();

            // 4. Flash Sequence
            textContainer.innerText = "Look at the camera...";

            // Initial Black (0.5s)
            await new Promise(r => setTimeout(r, 500));

            let flashOffset = 0;

            for (const color of sequence) {
                overlay.style.backgroundColor = color;
                if (color === 'red') {
                    flashOffset = performance.now() - recordStartTime;
                }
                await new Promise(r => setTimeout(r, 500));
            }

            // End Black
            overlay.style.backgroundColor = 'black';
            await new Promise(r => setTimeout(r, 200));

            // Stop Recording
            this.mediaRecorder.stop();
            const recordingFinished = new Promise(resolve => this.mediaRecorder.onstop = resolve);
            await recordingFinished;

            // Cleanup
            this.stream.getTracks().forEach(track => track.stop());
            document.body.removeChild(overlay);
            document.head.removeChild(styleSheet); // Cleanup styles

            // 5. Create Blob and Send
            const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
            const file = new File([blob], "challenge.webm", { type: 'video/webm' });
            const formData = new FormData();
            formData.append('video_file', file);
            formData.append('flash_offset', flashOffset.toString());


            // Re-use overlay for "Verifying" state but remove video
            overlay.innerHTML = ''; // Clear video
            overlay.style.backgroundColor = 'rgba(0,0,0,0.9)';
            textContainer.innerText = "Analyzing Biometric Data...";
            overlay.appendChild(textContainer);
            document.body.appendChild(overlay); // Show "Verifying"

            // Setup Timeout (60s) to handle long processing
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);

            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const result = await response.json();

            return result;

        } catch (error) {
            console.error("DeepShield Error:", error);

            let errorMsg = error.message;
            if (error.name === 'AbortError') {
                errorMsg = "Connection timed out. Server took too long.";
            } else if (error instanceof TypeError) {
                errorMsg = "Network error or CORS issue when connecting to API.";
            }

            // Return error to UI instead of alerting
            return { is_liveness_verified: false, delta: 0, latency_ms: 0, message: errorMsg, error: "Client-Side Error" };
        } finally {
            if (overlay) {
                overlay.classList.add('hidden');
                overlay.style.display = 'none';
            }
            // Ensure overlay is always removed
            if (overlay && overlay.parentNode) {
                document.body.removeChild(overlay);
            }
            // Ensure styles are removed if they still exist
            if (styleSheet && styleSheet.parentNode) {
                document.head.removeChild(styleSheet);
            }
        }
    }
}

// Export instance
window.deepShield = new DeepShield();
