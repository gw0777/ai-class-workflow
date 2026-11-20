// Music Impact Controller - Main Application
class MusicImpactController {
    constructor() {
        this.audioContext = null;
        this.audioElement = null;
        this.source = null;
        this.analyser = null;
        this.gainNode = null;
        this.panNode = null;
        this.bassFilter = null;
        this.trebleFilter = null;
        this.convolver = null;
        this.dryGain = null;
        this.wetGain = null;
        this.isPlaying = false;
        this.animationId = null;

        this.initializeElements();
        this.setupEventListeners();
    }

    initializeElements() {
        // File input
        this.fileInput = document.getElementById('audioFile');
        this.uploadArea = document.getElementById('uploadArea');

        // Playback controls
        this.playBtn = document.getElementById('playBtn');
        this.pauseBtn = document.getElementById('pauseBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.progressBar = document.getElementById('progressBar');
        this.volumeSlider = document.getElementById('volumeSlider');
        this.volumeValue = document.getElementById('volumeValue');

        // Track info
        this.nowPlaying = document.getElementById('nowPlaying');
        this.trackName = document.getElementById('trackName');
        this.currentTimeEl = document.getElementById('currentTime');
        this.durationEl = document.getElementById('duration');

        // Effect controls
        this.effectsSection = document.getElementById('effectsSection');
        this.panSlider = document.getElementById('panSlider');
        this.panValue = document.getElementById('panValue');
        this.panBall = document.getElementById('panBall');
        this.bassSlider = document.getElementById('bassSlider');
        this.bassValue = document.getElementById('bassValue');
        this.trebleSlider = document.getElementById('trebleSlider');
        this.trebleValue = document.getElementById('trebleValue');
        this.reverbSlider = document.getElementById('reverbSlider');
        this.reverbValue = document.getElementById('reverbValue');
        this.spatialSlider = document.getElementById('spatialSlider');
        this.spatialValue = document.getElementById('spatialValue');

        // Visualizer
        this.visualizerSection = document.getElementById('visualizerSection');
        this.canvas = document.getElementById('visualizer');
        this.canvasCtx = this.canvas.getContext('2d');

        // Preset buttons
        this.presetButtons = document.querySelectorAll('.preset-btn');
    }

    setupEventListeners() {
        // File input
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Playback controls
        this.playBtn.addEventListener('click', () => this.play());
        this.pauseBtn.addEventListener('click', () => this.pause());
        this.stopBtn.addEventListener('click', () => this.stop());
        this.progressBar.addEventListener('input', (e) => this.seek(e));
        this.volumeSlider.addEventListener('input', (e) => this.updateVolume(e));

        // Effect controls
        this.panSlider.addEventListener('input', (e) => this.updatePan(e));
        this.bassSlider.addEventListener('input', (e) => this.updateBass(e));
        this.trebleSlider.addEventListener('input', (e) => this.updateTreble(e));
        this.reverbSlider.addEventListener('input', (e) => this.updateReverb(e));
        this.spatialSlider.addEventListener('input', (e) => this.updateSpatial(e));

        // Presets
        this.presetButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const preset = e.target.closest('.preset-btn').dataset.preset;
                this.applyPreset(preset);
            });
        });
    }

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Initialize audio context if not already done
        if (!this.audioContext) {
            this.initializeAudioContext();
        }

        // Create audio element
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement = null;
        }

        this.audioElement = new Audio();
        this.audioElement.src = URL.createObjectURL(file);

        // Connect audio nodes
        this.connectAudioNodes();

        // Update UI
        this.trackName.textContent = file.name;
        this.uploadArea.style.display = 'none';
        this.nowPlaying.style.display = 'block';
        this.effectsSection.style.display = 'block';
        this.visualizerSection.style.display = 'block';

        // Setup time update
        this.audioElement.addEventListener('loadedmetadata', () => {
            this.durationEl.textContent = this.formatTime(this.audioElement.duration);
        });

        this.audioElement.addEventListener('timeupdate', () => {
            this.updateProgress();
        });

        this.audioElement.addEventListener('ended', () => {
            this.stop();
        });

        // Auto play
        this.play();
    }

    initializeAudioContext() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

        // Create analyser for visualization
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;

        // Create gain node for volume
        this.gainNode = this.audioContext.createGain();
        this.gainNode.gain.value = 0.8;

        // Create stereo panner
        this.panNode = this.audioContext.createStereoPanner();
        this.panNode.pan.value = 0;

        // Create bass filter (low-shelf)
        this.bassFilter = this.audioContext.createBiquadFilter();
        this.bassFilter.type = 'lowshelf';
        this.bassFilter.frequency.value = 200;
        this.bassFilter.gain.value = 0;

        // Create treble filter (high-shelf)
        this.trebleFilter = this.audioContext.createBiquadFilter();
        this.trebleFilter.type = 'highshelf';
        this.trebleFilter.frequency.value = 3000;
        this.trebleFilter.gain.value = 0;

        // Create reverb effect
        this.createReverbEffect();
    }

    createReverbEffect() {
        // Create convolver for reverb
        this.convolver = this.audioContext.createConvolver();

        // Create impulse response for reverb
        const sampleRate = this.audioContext.sampleRate;
        const length = sampleRate * 2; // 2 seconds reverb
        const impulse = this.audioContext.createBuffer(2, length, sampleRate);

        for (let channel = 0; channel < 2; channel++) {
            const channelData = impulse.getChannelData(channel);
            for (let i = 0; i < length; i++) {
                channelData[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 2);
            }
        }

        this.convolver.buffer = impulse;

        // Create dry/wet mix
        this.dryGain = this.audioContext.createGain();
        this.wetGain = this.audioContext.createGain();
        this.dryGain.gain.value = 1;
        this.wetGain.gain.value = 0;
    }

    connectAudioNodes() {
        if (!this.source) {
            this.source = this.audioContext.createMediaElementSource(this.audioElement);
        }

        // Audio routing:
        // source -> bassFilter -> trebleFilter -> panNode -> analyser -> gainNode
        //                                              |
        //                                              +-> dryGain -> destination
        //                                              +-> convolver -> wetGain -> destination

        // Main chain
        this.source.connect(this.bassFilter);
        this.bassFilter.connect(this.trebleFilter);
        this.trebleFilter.connect(this.panNode);
        this.panNode.connect(this.analyser);
        this.analyser.connect(this.gainNode);

        // Dry signal
        this.gainNode.connect(this.dryGain);
        this.dryGain.connect(this.audioContext.destination);

        // Wet signal (reverb)
        this.gainNode.connect(this.convolver);
        this.convolver.connect(this.wetGain);
        this.wetGain.connect(this.audioContext.destination);
    }

    play() {
        if (!this.audioElement) return;

        // Resume audio context if suspended
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }

        this.audioElement.play();
        this.isPlaying = true;
        this.playBtn.style.display = 'none';
        this.pauseBtn.style.display = 'inline-block';
        this.playBtn.classList.add('playing');

        // Start visualizer
        this.visualize();
    }

    pause() {
        if (!this.audioElement) return;

        this.audioElement.pause();
        this.isPlaying = false;
        this.playBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';
        this.playBtn.classList.remove('playing');

        // Stop visualizer
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }

    stop() {
        if (!this.audioElement) return;

        this.audioElement.pause();
        this.audioElement.currentTime = 0;
        this.isPlaying = false;
        this.playBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';
        this.playBtn.classList.remove('playing');
        this.progressBar.value = 0;

        // Stop visualizer
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }

    seek(event) {
        if (!this.audioElement) return;

        const seekTime = (event.target.value / 100) * this.audioElement.duration;
        this.audioElement.currentTime = seekTime;
    }

    updateVolume(event) {
        const volume = event.target.value / 100;
        if (this.gainNode) {
            this.gainNode.gain.value = volume;
        }
        this.volumeValue.textContent = event.target.value + '%';
    }

    updatePan(event) {
        const panValue = event.target.value / 100; // -1 to 1

        if (this.panNode) {
            this.panNode.pan.value = panValue;
        }

        // Update display
        if (panValue < -0.1) {
            this.panValue.textContent = `LEFT ${Math.abs(Math.round(panValue * 100))}%`;
        } else if (panValue > 0.1) {
            this.panValue.textContent = `RIGHT ${Math.round(panValue * 100)}%`;
        } else {
            this.panValue.textContent = 'CENTER';
        }

        // Update visual ball
        const ballPosition = ((parseFloat(event.target.value) + 100) / 200) * 100;
        this.panBall.style.left = ballPosition + '%';
    }

    updateBass(event) {
        const bassValue = parseFloat(event.target.value);

        if (this.bassFilter) {
            this.bassFilter.gain.value = bassValue;
        }

        this.bassValue.textContent = `${bassValue} dB`;
    }

    updateTreble(event) {
        const trebleValue = parseFloat(event.target.value);

        if (this.trebleFilter) {
            this.trebleFilter.gain.value = trebleValue;
        }

        this.trebleValue.textContent = `${trebleValue > 0 ? '+' : ''}${trebleValue} dB`;
    }

    updateReverb(event) {
        const reverbValue = event.target.value / 100;

        if (this.dryGain && this.wetGain) {
            this.dryGain.gain.value = 1 - reverbValue * 0.7;
            this.wetGain.gain.value = reverbValue * 0.5;
        }

        this.reverbValue.textContent = `${event.target.value}%`;
    }

    updateSpatial(event) {
        const spatialValue = event.target.value / 100;

        // Spatial effect: enhance stereo width by adjusting reverb and slight panning variations
        if (this.wetGain) {
            this.wetGain.gain.value = Math.max(this.wetGain.gain.value, spatialValue * 0.3);
        }

        this.spatialValue.textContent = `${event.target.value}%`;
    }

    applyPreset(preset) {
        switch(preset) {
            case 'reset':
                this.panSlider.value = 0;
                this.bassSlider.value = 0;
                this.trebleSlider.value = 0;
                this.reverbSlider.value = 0;
                this.spatialSlider.value = 0;
                break;

            case 'bass':
                this.panSlider.value = 0;
                this.bassSlider.value = 15;
                this.trebleSlider.value = -3;
                this.reverbSlider.value = 10;
                this.spatialSlider.value = 20;
                break;

            case 'vocal':
                this.panSlider.value = 0;
                this.bassSlider.value = 3;
                this.trebleSlider.value = 6;
                this.reverbSlider.value = 25;
                this.spatialSlider.value = 15;
                break;

            case 'concert':
                this.panSlider.value = 0;
                this.bassSlider.value = 8;
                this.trebleSlider.value = 4;
                this.reverbSlider.value = 60;
                this.spatialSlider.value = 70;
                break;

            case 'dynamic':
                this.panSlider.value = 0;
                this.bassSlider.value = 12;
                this.trebleSlider.value = 8;
                this.reverbSlider.value = 30;
                this.spatialSlider.value = 50;
                break;
        }

        // Trigger updates
        this.updatePan({ target: this.panSlider });
        this.updateBass({ target: this.bassSlider });
        this.updateTreble({ target: this.trebleSlider });
        this.updateReverb({ target: this.reverbSlider });
        this.updateSpatial({ target: this.spatialSlider });
    }

    updateProgress() {
        if (!this.audioElement) return;

        const progress = (this.audioElement.currentTime / this.audioElement.duration) * 100;
        this.progressBar.value = progress;
        this.currentTimeEl.textContent = this.formatTime(this.audioElement.currentTime);
    }

    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';

        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    visualize() {
        if (!this.analyser) return;

        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const draw = () => {
            if (!this.isPlaying) return;

            this.animationId = requestAnimationFrame(draw);
            this.analyser.getByteFrequencyData(dataArray);

            const WIDTH = this.canvas.width;
            const HEIGHT = this.canvas.height;

            this.canvasCtx.fillStyle = 'rgb(15, 23, 42)';
            this.canvasCtx.fillRect(0, 0, WIDTH, HEIGHT);

            const barWidth = (WIDTH / bufferLength) * 2.5;
            let barHeight;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                barHeight = (dataArray[i] / 255) * HEIGHT;

                // Create gradient
                const gradient = this.canvasCtx.createLinearGradient(0, HEIGHT - barHeight, 0, HEIGHT);
                gradient.addColorStop(0, '#ec4899');
                gradient.addColorStop(0.5, '#8b5cf6');
                gradient.addColorStop(1, '#6366f1');

                this.canvasCtx.fillStyle = gradient;
                this.canvasCtx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);

                x += barWidth + 1;
            }
        };

        draw();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new MusicImpactController();
    console.log('🎵 Music Impact Controller initialized!');
});
