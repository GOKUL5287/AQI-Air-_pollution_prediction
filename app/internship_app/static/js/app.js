/**
 * TerraPulse — Cinematic Scroll Engine v2.0
 *
 * Architecture:
 *   1. FrameEngine — Preloads 227 JPG frames; renders on canvas using cover logic
 *   2. ScrollEngine — GSAP ScrollTrigger maps scroll progress → frame index
 *   3. SceneDirector — Manages scene-specific overlays + pinned story card animations
 *   4. TerraPulseApp — API calls, UI updates, ML simulator, Plotly charts
 *
 * Video Narrative:
 *   Frames 000–035 : Earth from space (sun, moon, birds, cities, trees)
 *   Frames 036–095 : Descent through clouds → 3D relief world map with monuments
 *   Frames 096–165 : Atlantic Ocean with sailing galleon ("ATLANTICUS")
 *   Frames 166–226 : Pull-back to scholar's glass globe on antique desk
 */

/* ─────────────────────────────────────────────────────────────────
   1. FRAME ENGINE
   ───────────────────────────────────────────────────────────────── */
class FrameEngine {
  constructor(canvasId, totalFrames, basePath) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.totalFrames = totalFrames;
    this.basePath = basePath;
    this.images = new Array(totalFrames).fill(null);
    this.loaded = 0;
    this.failed = 0;
    this.currentIdx = 0;
    this.ready = false;

    if (!this.canvas) return;
    this._resize();
    window.addEventListener('resize', () => this._resize());
    this._preload();
  }

  _resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
    this._draw(this.currentIdx);
  }

  _preload() {
    for (let i = 0; i < this.totalFrames; i++) {
      const img = new Image();
      const n = String(i).padStart(3, '0');
      img.src = `${this.basePath}/frame_${n}.jpg`;
      img.onload = () => {
        this.loaded++;
        if (i === this.currentIdx) this._draw(i);
        this._settleFrameLoad();
      };
      img.onerror = () => {
        this.failed++;
        this._settleFrameLoad();
      };
      this.images[i] = img;
    }
  }

  _settleFrameLoad() {
    const settled = this.loaded + this.failed;
    const pct = Math.round((settled / this.totalFrames) * 100);
    document.dispatchEvent(new CustomEvent('frameProgress', { detail: pct }));

    if (settled === this.totalFrames) {
      this.ready = true;
      document.dispatchEvent(new CustomEvent('framesReady', {
        detail: { loaded: this.loaded, failed: this.failed }
      }));
    }
  }

  _draw(idx) {
    if (!this.ctx) return;
    const img = this.images[idx];
    if (!img || !img.complete || img.naturalWidth === 0) return;

    this.currentIdx = idx;
    const cw = this.canvas.width, ch = this.canvas.height;
    const iw = img.naturalWidth, ih = img.naturalHeight;
    const cRatio = cw / ch, iRatio = iw / ih;

    let rw, rh, ox, oy;
    if (cRatio > iRatio) {
      rw = cw; rh = cw / iRatio; ox = 0; oy = (ch - rh) / 2;
    } else {
      rh = ch; rw = ch * iRatio; ox = (cw - rw) / 2; oy = 0;
    }

    // Clear to dark background first
    this.ctx.fillStyle = '#020810';
    this.ctx.fillRect(0, 0, cw, ch);
    this.ctx.drawImage(img, ox, oy, rw, rh);

    // Update frame counter in navbar
    const el = document.getElementById('frame-display');
    if (el) el.textContent = String(idx + 1).padStart(3, '0');
  }

  seekProgress(progress) {
    const target = Math.min(
      this.totalFrames - 1,
      Math.max(0, Math.floor(progress * (this.totalFrames - 1)))
    );
    if (target !== this.currentIdx) this._draw(target);
    return target;
  }

  seekFrame(frame) {
    const target = Math.min(this.totalFrames - 1, Math.max(0, Math.round(frame)));
    if (target !== this.currentIdx) this._draw(target);
    return target;
  }
}

class CloudPointerEffect {
  constructor(canvasId, frameEngine) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas?.getContext('2d');
    this.frameEngine = frameEngine;
    this.puffs = [];
    this.ripples = [];
    this.pointer = { x: 0, y: 0 };
    this.lastPointer = null;
    this.lastFrameTime = performance.now();

    if (!this.canvas || !this.ctx) return;
    this._resize();
    window.addEventListener('resize', () => this._resize());
    window.addEventListener('pointermove', (event) => this._onPointerMove(event), { passive: true });
    window.addEventListener('pointerdown', (event) => this._onPointerDown(event), { passive: true });
    this._animate();
  }

  _resize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    this.canvas.width = Math.round(window.innerWidth * ratio);
    this.canvas.height = Math.round(window.innerHeight * ratio);
    this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  _isCloudScene() {
    return this.frameEngine.currentIdx >= 36 && this.frameEngine.currentIdx <= 95;
  }

  _addPuffs(x, y, count, driftX = 0, driftY = 0, strength = 1) {
    for (let index = 0; index < count; index++) {
      this.puffs.push({
        x: x + (Math.random() - 0.5) * 42,
        y: y + (Math.random() - 0.5) * 30,
        vx: driftX * 0.035 + (Math.random() - 0.5) * 16,
        vy: driftY * 0.035 + (Math.random() - 0.5) * 12,
        radius: (34 + Math.random() * 56) * strength,
        life: 0,
        duration: 1.1 + Math.random() * 0.8,
        strength
      });
    }
    if (this.puffs.length > 90) this.puffs.splice(0, this.puffs.length - 90);
  }

  _onPointerMove(event) {
    const pointer = { x: event.clientX, y: event.clientY };
    if (!this._isCloudScene()) {
      this.lastPointer = pointer;
      return;
    }

    if (this.lastPointer) {
      const dx = pointer.x - this.lastPointer.x;
      const dy = pointer.y - this.lastPointer.y;
      if (Math.hypot(dx, dy) > 8) this._addPuffs(pointer.x, pointer.y, 2, dx, dy, 1);
    }
    this.lastPointer = pointer;
  }

  _onPointerDown(event) {
    if (!this._isCloudScene()) return;
    const x = event.clientX;
    const y = event.clientY;
    this._addPuffs(x, y, 14, 0, 0, 1.25);
    this.ripples.push({ x, y, life: 0, duration: 0.9 });
  }

  _animate() {
    requestAnimationFrame(() => this._animate());
    const now = performance.now();
    const delta = Math.min((now - this.lastFrameTime) / 1000, 0.05);
    this.lastFrameTime = now;
    this.ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    if (!this._isCloudScene()) return;

    this.puffs = this.puffs.filter((puff) => {
      puff.life += delta;
      puff.x += puff.vx * delta;
      puff.y += puff.vy * delta;
      const progress = puff.life / puff.duration;
      if (progress >= 1) return false;
      const alpha = Math.sin(Math.PI * progress) * 0.12 * puff.strength;
      const gradient = this.ctx.createRadialGradient(puff.x, puff.y, 0, puff.x, puff.y, puff.radius);
      gradient.addColorStop(0, `rgba(230, 247, 255, ${alpha})`);
      gradient.addColorStop(0.5, `rgba(190, 225, 245, ${alpha * 0.45})`);
      gradient.addColorStop(1, 'rgba(190, 225, 245, 0)');
      this.ctx.fillStyle = gradient;
      this.ctx.fillRect(puff.x - puff.radius, puff.y - puff.radius, puff.radius * 2, puff.radius * 2);
      return true;
    });

    this.ripples = this.ripples.filter((ripple) => {
      ripple.life += delta;
      const progress = ripple.life / ripple.duration;
      if (progress >= 1) return false;
      this.ctx.beginPath();
      this.ctx.arc(ripple.x, ripple.y, 14 + progress * 118, 0, Math.PI * 2);
      this.ctx.strokeStyle = `rgba(205, 239, 255, ${(1 - progress) * 0.34})`;
      this.ctx.lineWidth = 1.5;
      this.ctx.stroke();
      return true;
    });
  }
}

/* ─────────────────────────────────────────────────────────────────
   2. SCENE DIRECTOR  (Overlays + pinned story card animations)
   ───────────────────────────────────────────────────────────────── */
class SceneDirector {
  constructor(frameEngine) {
    this.fe = frameEngine;
    this._registerGSAP();
  }

  _registerGSAP() {
    gsap.registerPlugin(ScrollTrigger);

    /* ── Master frame scrubber: maps total page scroll → frame 0…226 ── */
    let previousFrame = -1;
    ScrollTrigger.create({
      trigger: '#scroll-root',
      start: 'top top',
      end: 'bottom bottom',
      scrub: 0.25,
      onUpdate: (self) => {
        const steeringWheel = document.querySelector('#scroll-steering svg');
        if (steeringWheel) {
          steeringWheel.style.transform = `rotate(${(self.progress * 1080).toFixed(2)}deg)`;
        }

        const frame = this.fe.seekProgress(self.progress);
        if (frame === previousFrame) return;
        previousFrame = frame;
        this._updateOverlays(frame);
        this._updateHUD();
      }
    });

    /* ── Hero block: fade out as you scroll away ── */
    gsap.to('#hero-block', {
      opacity: 0, y: -50, scale: 0.97,
      scrollTrigger: {
        trigger: '#scene-hero',
        start: 'top top',
        end: 'center top',
        scrub: true
      }
    });

    /* ── Scroll hint: fade out early ── */
    gsap.to('#scroll-hint', {
      opacity: 0,
      scrollTrigger: {
        trigger: '#scene-hero',
        start: '5% top',
        end: '20% top',
        scrub: true
      }
    });

    /* ── SCENE 2: Cloud descent + World Map (pin) ── */
    this._pinScene('#scene-map', '#pin-map', [
      { el: '#map-card-a', inStart: 0.0, inEnd: 0.18, outStart: 0.35, outEnd: 0.52 },
      { el: '#map-card-b', inStart: 0.45, inEnd: 0.62, outStart: 0.82, outEnd: 0.98 }
    ]);

    /* ── SCENE 3: Ocean / Ship (pin) ── */
    this._pinScene('#scene-ocean', '#pin-ocean', [
      { el: '#ocean-card-a', inStart: 0.05, inEnd: 0.25, outStart: 0.70, outEnd: 0.90 }
    ]);

    /* ── SCENE 4: Scholar's globe (pin) ── */
    this._pinScene('#scene-globe', '#pin-globe', [
      { el: '#globe-card-a', inStart: 0.10, inEnd: 0.35, outStart: 0.72, outEnd: 0.92 }
    ]);

    /* ── Cinematic content reveals ── */
    document.querySelectorAll('.section-wrap > *').forEach(el => {
      gsap.fromTo(el,
        { opacity: 0, y: 48, filter: 'blur(10px)' },
        {
          opacity: 1, y: 0, filter: 'blur(0px)', ease: 'none',
          scrollTrigger: { trigger: el, start: 'top 88%', end: 'top 55%', scrub: true }
        }
      );
    });

    /* ── Marine cards stagger ── */
    const mcards = document.querySelectorAll('.mcard');
    if (mcards.length) {
      gsap.from(mcards, {
        opacity: 0, y: 30, stagger: 0.08,
        scrollTrigger: { trigger: '.marine-grid', start: 'top 80%', end: 'top 40%', scrub: true }
      });
    }
  }

  /**
   * Pin a scene's sticky container and animate cards in/out
   * based on their progress fractions within that section.
   */
  _pinScene(sectionSelector, pinSelector, cards) {
    const section = document.querySelector(sectionSelector);
    const pin = document.querySelector(pinSelector);
    if (!section || !pin) return;

    // Progress tracker
    ScrollTrigger.create({
      trigger: section,
      start: 'top top',
      end: 'bottom bottom',
      scrub: true,
      onUpdate: (self) => {
        const p = self.progress;
        cards.forEach(({ el, inStart, inEnd, outStart, outEnd }) => {
          const cardEl = document.querySelector(el);
          if (!cardEl) return;

          let opacity = 0, y = 40, scale = 0.95, blur = 8;

          if (p >= inStart && p < inEnd) {
            // Fading IN
            const t = (p - inStart) / (inEnd - inStart);
            opacity = t;
            y = 40 * (1 - t);
            scale = 0.95 + 0.05 * t;
            blur = 8 * (1 - t);
          } else if (p >= inEnd && p < outStart) {
            // FULLY VISIBLE
            opacity = 1; y = 0; scale = 1; blur = 0;
          } else if (p >= outStart && p < outEnd) {
            // Fading OUT
            const t = (p - outStart) / (outEnd - outStart);
            opacity = 1 - t;
            y = -30 * t;
            scale = 1 - 0.04 * t;
            blur = 4 * t;
          }

          cardEl.style.opacity = opacity;
          cardEl.style.transform = `translateY(${y}px) scale(${scale})`;
          cardEl.style.filter = `blur(${blur}px)`;
        });
      }
    });
  }

  /**
   * Update scene-specific color overlays based on current frame
   */
  _updateOverlays(frame) {
    const overlays = {
      'overlay-space': { start: 0, end: 35 },
      'overlay-map': { start: 36, end: 95 },
      'overlay-ocean': { start: 96, end: 165 },
      'overlay-globe': { start: 166, end: 226 }
    };

    Object.entries(overlays).forEach(([id, { start, end }]) => {
      const el = document.getElementById(id);
      if (!el) return;
      if (frame >= start && frame <= end) {
        const p = (frame - start) / (end - start);
        // Ease in and out
        const opacity = Math.sin(Math.PI * p) * 0.38;
        el.style.opacity = opacity;
      } else {
        el.style.opacity = 0;
      }
    });
  }

  _updateHUD() {
    if (window.app && window.app.currentStation) {
      const s = window.app.currentStation;
      const geoEl = document.getElementById('hud-geo');
      if (geoEl) {
        const lat = Math.abs(s.lat).toFixed(2);
        const lon = Math.abs(s.lon).toFixed(2);
        const ns = s.lat >= 0 ? 'N' : 'S';
        const ew = s.lon >= 0 ? 'E' : 'W';
        geoEl.textContent = `GEO: ${lat}°${ns}, ${lon}°${ew} · LIVE`;
      }
    }
  }
}

/* ─────────────────────────────────────────────────────────────────
   3. MAIN APPLICATION
   ───────────────────────────────────────────────────────────────── */
class TerraPulseApp {
  constructor() {
    this.currentStation = null;
    this.currentAirQuality = null;
    this.currentWeather = null;
    this.currentPrediction = null;
    this.currentMarine = null;
    this.allStations = [];
    this.countries = [];
    this.selectedLocality = '';
    this.stationPage = 1;
    this.stationDisplayLimit = 6;
    this.stationTotal = 0;
    this.locationRequestId = 0;
    this._searchTimer = null;

    this._init();
  }

  async _init() {
    // 1. Boot frame engine
    this.frameEngine = new FrameEngine('frame-canvas', 227, '/static/assets/frames');
    this.cloudPointerEffect = new CloudPointerEffect('cloud-effect-canvas', this.frameEngine);

    // 2. Boot scene director (GSAP)
    this.sceneDirector = new SceneDirector(this.frameEngine);

    // 3. Navbar scroll-class
    this._navbarScroll();

    // 4. Load station list
    await this._loadStations();

    // 5. Bind UI events
    this._bindEvents();

    // 6. Select default location
    const defaultStation = this.allStations.find(s => s.country_code === 'IN')
      || this.allStations[0]
      || { station_id: 'DEFAULT', name: 'New Delhi', city: 'New Delhi', country: 'India', country_code: 'IN', lat: 28.61, lon: 77.21, is_coastal: false };

    await this.selectLocation(defaultStation);

    // 7. ML simulator
    this._initSimulator();

    // 8. Integrated history dashboard and persistent location map
    this._initSeasonalDashboard();
    this._initMapOverlay();
  }

  _navbarScroll() {
    const nav = document.getElementById('navbar');
    if (!nav) return;
    window.addEventListener('scroll', () => {
      if (window.scrollY > 60) nav.classList.add('scrolled');
      else nav.classList.remove('scrolled');
    }, { passive: true });
  }

  async _loadStations() {
    try {
      const resp = await fetch('/api/regions/countries');
      const json = await resp.json();
      this.countries = json.data || [];
      const countrySelect = document.getElementById('country-select');
      if (!countrySelect || !this.countries.length) return;
      countrySelect.innerHTML = this.countries.map(country =>
        `<option value="${this._escapeHTML(country.code)}">${this._escapeHTML(country.name)} (${this._escapeHTML(country.code)})</option>`
      ).join('');
      const defaultCode = this.countries.some(country => country.code === 'IN') ? 'IN' : this.countries[0].code;
      countrySelect.value = defaultCode;
      await this._loadCountryStations(defaultCode);
    } catch (e) {
      console.warn('[TerraPulse] Station load failed:', e);
    }
  }

  async _loadCountryStations(countryCode, page = 1, append = false) {
    const localitySelect = document.getElementById('locality-select');
    const loadMore = document.getElementById('load-more-stations');
    const resultsMeta = document.getElementById('station-results-meta');
    if (localitySelect) localitySelect.disabled = true;
    if (!append) {
      this.selectedLocality = '';
      this.stationPage = 1;
      this.stationDisplayLimit = 6;
      this.allStations = [];
      this.currentPrediction = null;
      this.currentWeather = null;
      this.currentAirQuality = null;
      if (resultsMeta) resultsMeta.textContent = 'Loading OpenAQ monitoring locations...';
    }
    try {
      const [stationResponse, stateResponse] = await Promise.all([
        fetch(`/api/regions/${encodeURIComponent(countryCode)}/stations?page=${page}&limit=1000`),
        page === 1 ? fetch(`/api/regions/${encodeURIComponent(countryCode)}/states`) : Promise.resolve(null)
      ]);
      const stationJson = await stationResponse.json();
      if (!stationResponse.ok || stationJson.status !== 'success') throw new Error(stationJson.message || 'Station request failed');
      const loadedStations = stationJson.data || [];
      this.allStations = append ? this.allStations.concat(loadedStations) : loadedStations;
      this.stationPage = page;
      this.stationTotal = stationJson.total;

      if (localitySelect && stateResponse) {
        const stateJson = await stateResponse.json();
        const localities = (stateJson.data || []).map(state => state.name).filter(Boolean);
        localitySelect.innerHTML = localities.length
          ? '<option value="">All available states / localities</option>' +
          localities.map(locality => `<option value="${this._escapeHTML(locality)}">${this._escapeHTML(locality)}</option>`).join('')
          : '<option value="">OpenAQ has no state / locality values</option>';
        localitySelect.disabled = localities.length === 0;
      }
      if (localitySelect && loadedStations.length) {
        const available = new Set(Array.from(localitySelect.options, option => option.value));
        loadedStations.forEach(station => {
          const locality = station.locality;
          if (!locality || locality === 'Unspecified locality' || available.has(locality)) return;
          localitySelect.add(new Option(locality, locality));
          available.add(locality);
        });
        localitySelect.disabled = localitySelect.options.length <= 1;
      }
      if (resultsMeta) {
        const totalLabel = Number.isFinite(Number(this.stationTotal)) ? `${this.stationTotal}` : `${this.allStations.length}+`;
        resultsMeta.textContent = `${this.allStations.length} of ${totalLabel} OpenAQ locations loaded`;
      }
      this._renderCountryFocus(this.countries.find(country => country.code === countryCode)?.name || countryCode, countryCode);
      return this.allStations;
    } catch (error) {
      if (resultsMeta) resultsMeta.textContent = 'OpenAQ locations are unavailable right now.';
      if (loadMore) loadMore.hidden = true;
      console.warn('[TerraPulse] Country station load failed:', error);
      return [];
    } finally {
      if (localitySelect) localitySelect.disabled = localitySelect.options.length <= 1;
    }
  }

  _bindEvents() {
    // Search input
    const inp = document.getElementById('region-search-input');
    const drop = document.getElementById('search-dropdown-menu');
    if (inp) {
      inp.addEventListener('input', (e) => {
        clearTimeout(this._searchTimer);
        const q = e.target.value.trim();
        if (q.length < 2) { drop?.classList.remove('active'); return; }
        this._searchTimer = setTimeout(async () => {
          const countryMatches = this.countries.filter(country =>
            country.name.toLowerCase().includes(q.toLowerCase()) || country.code.toLowerCase() === q.toLowerCase()
          ).slice(0, 4).map(country => ({
            kind: 'country', country_code: country.code, title: country.name, subtitle: `OpenAQ country · ${country.code}`
          }));
          const stationMatches = this.allStations.filter(station =>
            `${station.station_name} ${station.city} ${station.locality}`.toLowerCase().includes(q.toLowerCase())
          ).slice(0, 8).map(station => ({
            kind: 'station', station_id: station.station_id, title: station.station_name,
            subtitle: `${station.locality || 'State / locality not supplied'} · ${station.country}`
          }));
          this._renderSearch(countryMatches.concat(stationMatches));
        }, 250);
      });
      document.addEventListener('click', (e) => {
        if (!inp.contains(e.target) && !drop?.contains(e.target)) drop?.classList.remove('active');
      });
    }

    document.getElementById('country-select')?.addEventListener('change', async (event) => {
      const countryCode = event.target.value;
      const stations = await this._loadCountryStations(countryCode);
      if (stations?.length) await this.selectLocation(stations[0]);
    });

    document.getElementById('locality-select')?.addEventListener('change', async (event) => {
      this.selectedLocality = event.target.value;
      this.stationDisplayLimit = 6;
      const country = this.countries.find(item => item.code === document.getElementById('country-select')?.value);
      this._renderCountryFocus(country?.name || '', country?.code || '');
      const station = this.allStations.find(item => !this.selectedLocality || item.locality === this.selectedLocality);
      if (station) await this.selectLocation(station);
    });

    document.getElementById('load-more-stations')?.addEventListener('click', async () => {
      const button = document.getElementById('load-more-stations');
      if (button) button.disabled = true;
      const code = document.getElementById('country-select')?.value;
      const visibleLocations = this.allStations.filter(station =>
        !this.selectedLocality || station.locality === this.selectedLocality
      );
      if (this.stationDisplayLimit < visibleLocations.length) {
        this.stationDisplayLimit += 6;
        const country = this.countries.find(item => item.code === code);
        this._renderCountryFocus(country?.name || '', code || '');
      } else if (code) {
        this.stationDisplayLimit += 6;
        await this._loadCountryStations(code, this.stationPage + 1, true);
      }
      if (button) button.disabled = false;
    });

    // Clickable region cards
    document.addEventListener('click', (event) => {
      const card = event.target.closest('.station-card');
      if (!card) return;
      const stationId = card.dataset.stationId;
      const station = this.allStations.find(s => s.station_id === stationId);
      if (station) this.selectLocation(station);
    });

    // Chart tabs
    document.querySelectorAll('.ctab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.ctab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this._renderChart(tab.dataset.chartView);
      });
    });

    document.getElementById('seasonal-city')?.addEventListener('change', (event) => {
      const yearSelect = document.getElementById('seasonal-year');
      if (yearSelect) yearSelect.value = '';
      this._loadSeasonalDashboard(event.target.value);
    });
    document.getElementById('seasonal-year')?.addEventListener('change', () => {
      const city = document.getElementById('seasonal-city')?.value;
      if (city) this._loadSeasonalDashboard(city);
    });
    document.getElementById('seasonal-download')?.addEventListener('click', () => {
      this._downloadSeasonalCsv();
    });
    document.querySelectorAll('.seasonal-tab').forEach((tab) => {
      tab.addEventListener('click', () => this._showSeasonalTab(tab.dataset.seasonalTab));
      tab.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
        const tabs = [...document.querySelectorAll('.seasonal-tab')];
        const currentIndex = tabs.indexOf(tab);
        const direction = event.key === 'ArrowRight' ? 1 : -1;
        const next = tabs[(currentIndex + direction + tabs.length) % tabs.length];
        event.preventDefault();
        this._showSeasonalTab(next.dataset.seasonalTab);
        next.focus();
      });
    });
  }

  _initMapOverlay() {
    const dialog = document.getElementById('station-map-dialog');
    const launcher = document.getElementById('map-launcher');
    if (!dialog || !launcher) return;

    launcher.addEventListener('click', async () => {
      if (!window.L) {
        document.getElementById('map-location-count').textContent =
          'The map library did not load. Check your connection and reload the page.';
      }
      dialog.showModal();
      if (window.L) {
        await this._loadMapLocations();
        this._renderStationMap();
        this._loadMapSensorStatus();
        window.setTimeout(() => this.map?.invalidateSize(), 120);
      }
    });
    document.getElementById('map-close')?.addEventListener('click', () => dialog.close());
    document.getElementById('map-location-search-button')?.addEventListener('click', () => {
      this._findMapLocation();
    });
    document.getElementById('map-location-search')?.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      this._findMapLocation();
    });
    dialog.addEventListener('click', (event) => {
      const target = event.target instanceof Element
        ? event.target.closest('.map-popup-select')
        : null;
      if (target) {
        const station = this.mapLocations?.find((item) =>
          String(item.station_id) === target.dataset.stationId
        );
        if (station) {
          dialog.close();
          this._openMapStation(station);
        }
        return;
      }
      if (event.target === dialog) dialog.close();
    });
  }

  _findMapLocation() {
    const input = document.getElementById('map-location-search');
    const query = input?.value.trim().toLocaleLowerCase();
    if (!query || !this.mapLocations?.length) return;
    const station = this.mapLocations.find((item) =>
      [item.station_name, item.city, item.locality, item.country, item.country_code]
        .some((value) => String(value || '').toLocaleLowerCase().includes(query))
    );
    const marker = station && this.mapMarkers?.get(String(station.station_id));
    if (!station || !marker) {
      input.setCustomValidity('No matching monitoring location was found.');
      input.reportValidity();
      return;
    }
    input.setCustomValidity('');
    this.map.setView([Number(station.lat), Number(station.lon)], 10);
    marker.openPopup();
  }

  async _openMapStation(station) {
    await this.selectLocation(station);
    document.getElementById('scene-command')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async _loadMapLocations() {
    if (this.mapLocations?.length) return;
    const count = document.getElementById('map-location-count');
    if (count) count.textContent = 'Loading worldwide OpenAQ sensor locations…';

    try {
      const firstResponse = await fetch('/api/regions/stations?page=1&limit=1000');
      const firstPage = await firstResponse.json();
      if (!firstResponse.ok || firstPage.status !== 'success') {
        throw new Error(firstPage.message || 'Could not load global sensor locations.');
      }
      const pages = [firstPage];
      const totalPages = Number.isFinite(Number(firstPage.total))
        ? Math.ceil(Number(firstPage.total) / 1000)
        : null;
      let nextPage = 2;
      while (totalPages === null ? pages[pages.length - 1].page_count === 1000 : nextPage <= totalPages) {
        const batch = Array.from(
          { length: Math.min(4, totalPages === null ? 4 : totalPages - nextPage + 1) },
          (_, index) => nextPage + index
        );
        const batchResults = await Promise.all(batch.map(async (page) => {
          const response = await fetch(`/api/regions/stations?page=${page}&limit=1000`);
          const result = await response.json();
          if (!response.ok || result.status !== 'success') {
            throw new Error(result.message || `Could not load global sensor page ${page}.`);
          }
          return result;
        }));
        pages.push(...batchResults);
        nextPage += batch.length;
        const loaded = pages.reduce((total, page) => total + (page.data || []).length, 0);
        if (count) count.textContent = `Loading worldwide sensor locations… ${loaded.toLocaleString()} loaded`;
        if (totalPages === null && batchResults[batchResults.length - 1].page_count < 1000) break;
      }
      this.mapLocations = pages.flatMap((page) => page.data || []).map((station) => ({
        ...station,
        station_id: String(station.station_id || ''),
      })).filter((station) =>
        station.lat !== null && station.lon !== null
        && Number.isFinite(Number(station.lat)) && Number.isFinite(Number(station.lon))
        && Math.abs(Number(station.lat)) <= 90 && Math.abs(Number(station.lon)) <= 180
      );
      if (!this.mapLocations.length) {
        throw new Error('No global monitoring locations with coordinates are available.');
      }
    } catch (error) {
      this.mapLocations = [];
      if (count) count.textContent = `Map locations could not be loaded: ${error.message}`;
      console.error('[TerraPulse] Global sensor locations failed:', error);
    }
  }

  async _loadMapSensorStatus() {
    const status = document.getElementById('map-sensor-status');
    if (!status) return;
    try {
      const response = await fetch('/api/air-quality/live-status');
      const result = await response.json();
      if (!response.ok || result.status !== 'success') {
        throw new Error(result.message || 'Live sensor status is unavailable.');
      }
      status.textContent = result.live_available
        ? 'OpenAQ is configured. Select a marker to load its latest sensor readings.'
        : 'OpenAQ API key is not configured. Reference locations are not live sensor readings.';
    } catch (error) {
      status.textContent = `Unable to check live sensor availability: ${error.message}`;
    }
  }

  _mapSensorPopupContent(station, state, data = null, error = '') {
    const observed = data?.observed_measurements || {};
    const units = data?.units || {};
    const hasLiveReadings = data?.status === 'LIVE' && Object.keys(observed).length > 0;
    const names = { pm25: 'PM2.5', pm10: 'PM10', no2: 'NO₂', co: 'CO', so2: 'SO₂', o3: 'O₃' };
    const sensorNames = (station.parameters || []).map((parameter) => {
      const key = String(parameter).toLowerCase().replace(/[.\s_-]/g, '');
      return names[key] || parameter;
    });
    const readings = Object.entries(observed).map(([key, value]) => {
      const numericValue = Number(value);
      if (!Number.isFinite(numericValue)) return '';
      return `<li>${this._escapeHTML(names[key] || key)}: ${numericValue} ${this._escapeHTML(units[key] || '')}</li>`;
    }).filter(Boolean).join('');
    const timestamp = data?.timestamp ? new Date(data.timestamp) : null;
    const timeLabel = timestamp && !Number.isNaN(timestamp.valueOf())
      ? timestamp.toLocaleString()
      : '';
    const sensorMessage = error
      ? this._escapeHTML(error)
      : state === 'loading'
        ? 'Loading latest sensor readings…'
        : hasLiveReadings
          ? `Observed at ${this._escapeHTML(data.station_name || 'nearby OpenAQ station')}${timeLabel ? ` · ${this._escapeHTML(timeLabel)}` : ''}`
          : data?.provenance === 'DEMONSTRATION'
            ? 'Reference/demo values only; no live sensor reading.'
            : data?.status === 'NO_LATEST_MEASUREMENTS'
              ? 'No current sensor readings are available for this station.'
              : 'No live sensor observation is available.';
    const liveClass = hasLiveReadings ? 'is-live' : 'is-unavailable';
    return `<strong>${this._escapeHTML(station.station_name || station.name || station.city || 'Monitoring location')}</strong>` +
      `<br>${this._escapeHTML(station.city || '')}, ${this._escapeHTML(station.country || '')}` +
      `<br><small>${this._escapeHTML(station.provider || 'Location provider not specified')}</small>` +
      `${sensorNames.length ? `<br><small>Available sensors: ${this._escapeHTML(sensorNames.join(', '))}</small>` : ''}` +
      `<br><small>${Number(station.lat).toFixed(4)}, ${Number(station.lon).toFixed(4)}</small>` +
      `<div class="map-sensor-reading ${liveClass}" aria-live="polite">${sensorMessage}` +
      `${readings ? `<ul>${readings}</ul>` : ''}</div>` +
      `<button class="map-popup-refresh" type="button">Refresh sensor reading</button>` +
      `<br><button class="map-popup-select" type="button" data-station-id="${this._escapeHTML(station.station_id || '')}">Load station telemetry</button>`;
  }

  _openSeasonalDashboard(station) {
    const section = document.getElementById('scene-seasonal');
    const citySelect = document.getElementById('seasonal-city');
    const stationCities = [station.city, station.locality, station.name, station.station_name]
      .filter(Boolean)
      .map((name) => String(name).trim());
    const cityAliases = stationCities.flatMap((city) => {
      const normalized = city.toLowerCase();
      if (normalized === 'new delhi') return [city, 'Delhi'];
      if (normalized === 'delhi') return [city, 'New Delhi'];
      return [city];
    });
    const matchingOption = citySelect && [...citySelect.options].find((option) =>
      cityAliases.some((city) => option.value.toLowerCase() === city.toLowerCase())
    );

    if (matchingOption && citySelect.value !== matchingOption.value) {
      citySelect.value = matchingOption.value;
      const yearSelect = document.getElementById('seasonal-year');
      if (yearSelect) yearSelect.value = '';
      this._loadSeasonalDashboard(matchingOption.value);
    }

    if (!section) return;
    window.history.replaceState(null, '', '#scene-seasonal');
    window.setTimeout(() => {
      section.scrollIntoView({ behavior: 'instant', block: 'start' });
    }, 0);
  }

  _renderStationMap() {
    const count = document.getElementById('map-location-count');
    const locations = (this.mapLocations || []).filter((station) =>
      station.lat !== null && station.lat !== '' && station.lon !== null && station.lon !== ''
      && Number.isFinite(Number(station.lat)) && Number.isFinite(Number(station.lon))
      && Math.abs(Number(station.lat)) <= 90 && Math.abs(Number(station.lon)) <= 180
    );
    if (!locations.length) {
      if (count) {
        count.textContent = this.mapLocations?.length
          ? 'Loaded locations do not include valid coordinates.'
          : count.textContent || 'Worldwide monitoring locations could not be loaded. Close the map and open it again to retry.';
      }
      return;
    }

    if (!this.map) {
      this.map = window.L.map('station-map', {
        scrollWheelZoom: true,
        touchZoom: true,
        doubleClickZoom: true,
        preferCanvas: true
      }).setView([20, 0], 2);
      window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(this.map);
      this.mapLayer = window.L.featureGroup().addTo(this.map);
    }

    this.mapLayer.clearLayers();
    this.mapMarkers = new Map();
    const searchInput = document.getElementById('map-location-search');
    if (searchInput) searchInput.setCustomValidity('');
    locations.forEach((station) => {
      const lat = Number(station.lat);
      const lon = Number(station.lon);
      const isSelected = station.station_id === this.currentStation?.station_id;
      const marker = window.L.circleMarker([lat, lon], {
        radius: isSelected ? 9 : 6,
        color: isSelected ? '#f7d49a' : '#809197',
        fillColor: '#9ba9ad',
        fillOpacity: 0.9,
        weight: 2
      }).addTo(this.mapLayer);
      const cacheKey = String(station.station_id || `${lat},${lon}`);
      this.mapMarkers.set(cacheKey, marker);
      marker.bindPopup(this._mapSensorPopupContent(station, 'idle'));
      marker.on('popupopen', (event) => {
        const popup = event.popup;
        const render = (state, data = null, error = '') => {
          popup.setContent(this._mapSensorPopupContent(station, state, data, error));
          const element = popup.getElement();
          element?.querySelector('.map-popup-refresh')?.addEventListener('click', async (clickEvent) => {
            clickEvent.stopPropagation();
            await loadReading(true);
          });
          popup.update();
        };
        const loadReading = async (forceRefresh = false) => {
          const cache = this.mapReadingCache || (this.mapReadingCache = new Map());
          const cached = cache.get(cacheKey);
          if (!forceRefresh && cached && Date.now() - cached.fetchedAt < 15 * 60 * 1000) {
            render('loaded', cached.data);
            this._updateMapMarkerReading(marker, cached.data, isSelected);
            return;
          }
          render('loading');
          try {
            const query = new URLSearchParams({
              lat: String(lat),
              lon: String(lon),
              station_id: String(station.station_id || ''),
              ...(forceRefresh ? { refresh: '1' } : {})
            });
            const response = await fetch(`/api/air-quality/current?${query}`);
            const result = await response.json();
            if (!response.ok || result.status !== 'success') {
              throw new Error(result.message || 'Unable to load sensor readings.');
            }
            cache.set(cacheKey, { fetchedAt: Date.now(), data: result.data });
            render('loaded', result.data);
            this._updateMapMarkerReading(marker, result.data, isSelected);
          } catch (error) {
            render('error', null, `Sensor readings could not be loaded: ${error.message}`);
          }
        };
        loadReading();
      });
    });
    if (count) {
      count.textContent = `${locations.length.toLocaleString()} worldwide monitoring locations. Select a marker to view available sensors and latest readings.`;
    }
  }

  _updateMapMarkerReading(marker, data, isSelected) {
    const hasLiveReadings = data?.status === 'LIVE'
      && Object.keys(data.observed_measurements || {}).length > 0;
    marker.setStyle({
      color: isSelected ? '#f7d49a' : hasLiveReadings ? '#41c9a5' : '#809197',
      fillColor: hasLiveReadings ? '#41c9a5' : '#9ba9ad'
    });
  }

  async _initSeasonalDashboard() {
    await this._loadSeasonalDashboard();
  }

  async _loadSeasonalDashboard(city) {
    const status = document.getElementById('seasonal-status');
    const citySelect = document.getElementById('seasonal-city');
    const yearSelect = document.getElementById('seasonal-year');
    if (!status || !citySelect || !yearSelect) return;
    const requestId = (this.seasonalRequestId || 0) + 1;
    this.seasonalRequestId = requestId;

    const params = new URLSearchParams();
    if (city) params.set('city', city);
    if (yearSelect.value) params.set('year', yearSelect.value);
    status.textContent = 'Loading historical AQI summaries…';
    status.classList.remove('is-error');

    try {
      const response = await fetch(`/api/analytics/seasonal?${params.toString()}`);
      const result = await response.json();
      if (!response.ok || result.status !== 'success') {
        throw new Error(result.message || `Seasonal history request failed (${response.status}).`);
      }
      if (requestId !== this.seasonalRequestId) return;

      const data = result.data;
      this.seasonalData = data;
      if (document.activeElement !== citySelect) {
        citySelect.innerHTML = data.cities.map((name) =>
          `<option value="${this._escapeHTML(name)}">${this._escapeHTML(name)}</option>`
        ).join('');
        citySelect.value = data.city;
      }
      if (document.activeElement !== yearSelect || !yearSelect.options.length) {
        yearSelect.innerHTML = [...data.years].reverse().map((value) =>
          `<option value="${value}">${value}</option>`
        ).join('');
        yearSelect.value = String(data.year);
      }
      citySelect.disabled = false;
      yearSelect.disabled = false;
      document.getElementById('seasonal-download').disabled = !data.monthly.length;
      this._renderSeasonalDashboard(data);
      const summary = data.summary;
      status.textContent = `${data.city} · ${summary.rows.toLocaleString()} hourly station records · ${summary.stations} stations · ${summary.start.slice(0, 10)} to ${summary.end.slice(0, 10)}`;
      document.getElementById('seasonal-summary').hidden = false;
    } catch (error) {
      if (requestId !== this.seasonalRequestId) return;
      status.textContent = error.message;
      status.classList.add('is-error');
      citySelect.disabled = true;
      yearSelect.disabled = true;
      document.getElementById('seasonal-download').disabled = true;
      console.error('[TerraPulse] Seasonal history failed:', error);
    }
  }

  _renderSeasonalDashboard(data) {
    if (!window.Plotly) return;
    const pollutantColors = {
      'PM2.5': '#b6e8e5', 'PM10': '#f7d49a', 'NO2': '#91b7e5',
      'CO': '#d0c4df', 'SO2': '#efbdc7', 'O3': '#b9dfc8'
    };
    const layout = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(5,13,20,0.28)',
      font: { family: 'DM Sans, sans-serif', color: '#d0dcda', size: 12 },
      margin: { l: 48, r: 24, t: 18, b: 48 },
      xaxis: { gridcolor: 'rgba(197,221,223,0.1)', linecolor: 'rgba(197,221,223,0.18)' },
      yaxis: { gridcolor: 'rgba(197,221,223,0.1)', linecolor: 'rgba(197,221,223,0.18)' },
      legend: { orientation: 'h', y: 1.12, x: 0, bgcolor: 'rgba(0,0,0,0)' }
    };
    const config = { responsive: true, displayModeBar: false };

    document.getElementById('seasonal-mean-aqi').textContent =
      Number.isFinite(data.summary.mean_aqi) ? data.summary.mean_aqi.toFixed(1) : '—';
    document.getElementById('seasonal-stations').textContent = data.summary.stations.toLocaleString();
    document.getElementById('seasonal-records').textContent = data.summary.rows.toLocaleString();
    document.getElementById('seasonal-period').textContent =
      `${data.summary.start.slice(0, 4)}–${data.summary.end.slice(0, 4)}`;

    window.Plotly.react('seasonal-monthly-chart', [{
      x: data.monthly.map((row) => row.date),
      y: data.monthly.map((row) => row.AQI),
      customdata: data.monthly.map((row) => row.observations),
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Monthly mean AQI',
      line: { color: '#b6e8e5', width: 2.5 },
      marker: { size: 5 },
      connectgaps: false,
      hovertemplate: '%{x|%b %Y}<br>Mean AQI: %{y:.1f}<br>Valid AQI records: %{customdata:,}<extra></extra>'
    }], {
      ...layout,
      xaxis: { ...layout.xaxis, title: 'Month', type: 'date' },
      yaxis: { ...layout.yaxis, title: 'AQI' }
    }, config);

    const seasons = data.seasons;
    const pollutants = Object.keys(pollutantColors);
    window.Plotly.react('seasonal-pollutant-chart', pollutants.map((pollutant) => ({
      x: seasons.map((row) => row.season),
      y: seasons.map((row) => row.pollutant_index[pollutant]),
      name: pollutant,
      type: 'bar',
      marker: { color: pollutantColors[pollutant] },
      hovertemplate: `${pollutant}<br>%{x}<br>Index: %{y:.1f}<extra></extra>`
    })), {
      ...layout,
      barmode: 'group',
      xaxis: { ...layout.xaxis, title: 'Season' },
      yaxis: { ...layout.yaxis, title: 'Index (all-season mean = 100)', rangemode: 'tozero' }
    }, config);

    window.Plotly.react('seasonal-weather-chart', [
      {
        x: seasons.map((row) => row.season), y: seasons.map((row) => row.Temperature_C),
        name: 'Temperature (°C)', type: 'scatter', mode: 'lines+markers',
        line: { color: '#f7d49a', width: 2.5 }
      },
      {
        x: seasons.map((row) => row.season), y: seasons.map((row) => row.Wind_Speed_kmh),
        name: 'Wind (km/h)', type: 'scatter', mode: 'lines+markers',
        line: { color: '#91b7e5', width: 2.5 }
      },
      {
        x: seasons.map((row) => row.season), y: seasons.map((row) => row.Relative_Humidity_pct),
        name: 'Humidity (%)', type: 'scatter', mode: 'lines+markers', yaxis: 'y2',
        line: { color: '#b9dfc8', width: 2, dash: 'dot' }
      }
    ], {
      ...layout,
      yaxis: { ...layout.yaxis, title: 'Temperature / wind' },
      yaxis2: { title: 'Humidity (%)', overlaying: 'y', side: 'right', showgrid: false },
      xaxis: { ...layout.xaxis, title: 'Season' }
    }, config);

    this._renderSeasonalCalendar(data);
    const qualityEntries = Object.entries(data.quality);
    window.Plotly.react('seasonal-quality-chart', [{
      x: qualityEntries.map(([, value]) => value),
      y: qualityEntries.map(([name]) => name),
      type: 'bar',
      orientation: 'h',
      marker: { color: qualityEntries.map(([name]) => name === 'AQI' ? '#f7d49a' : '#91b7e5') },
      hovertemplate: '%{y}: %{x:.1f}% missing<extra></extra>'
    }], {
      ...layout,
      margin: { ...layout.margin, l: 115 },
      xaxis: { ...layout.xaxis, title: 'Missing records (%)', range: [0, 100] },
      yaxis: { ...layout.yaxis, autorange: 'reversed' }
    }, config);
    this._showSeasonalTab(this.activeSeasonalTab || 'overview');
  }

  _showSeasonalTab(name) {
    this.activeSeasonalTab = name;
    document.querySelectorAll('.seasonal-tab').forEach((tab) => {
      const active = tab.dataset.seasonalTab === name;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
    });
    document.querySelectorAll('.seasonal-panel').forEach((panel) => {
      panel.hidden = panel.dataset.seasonalPanel !== name;
    });
    const panel = document.querySelector(`[data-seasonal-panel="${name}"]`);
    if (panel && window.Plotly) {
      window.setTimeout(() => {
        panel.querySelectorAll('.js-plotly-plot').forEach((chart) => window.Plotly.Plots.resize(chart));
      }, 0);
    }
  }

  _renderSeasonalCalendar(data) {
    const year = Number(data.year);
    const start = new Date(Date.UTC(year, 0, 1));
    const end = new Date(Date.UTC(year + 1, 0, 1));
    const dates = new Map(data.daily.map((item) => [item.date, item]));
    const weekCount = Math.ceil((Math.ceil((end - start) / 86400000) + start.getUTCDay()) / 7);
    const values = Array.from({ length: 7 }, () => Array(weekCount).fill(null));
    const custom = Array.from({ length: 7 }, () => Array(weekCount).fill(null));

    for (let date = new Date(start); date < end; date.setUTCDate(date.getUTCDate() + 1)) {
      const offset = Math.floor((date - start) / 86400000);
      const week = Math.floor((offset + start.getUTCDay()) / 7);
      const weekday = date.getUTCDay();
      const label = date.toISOString().slice(0, 10);
      const item = dates.get(label);
      values[weekday][week] = item?.aqi ?? null;
      custom[weekday][week] = item
        ? `${label}<br>Daily mean AQI: ${item.aqi === null ? 'no data' : item.aqi.toFixed(1)}<br>Hourly records: ${item.observations}`
        : `${label}<br>No AQI observation`;
    }

    window.Plotly.react('seasonal-calendar-chart', [{
      x: Array.from({ length: weekCount }, (_, index) => index + 1),
      y: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      z: values,
      customdata: custom,
      type: 'heatmap',
      colorscale: [
        [0, '#34d399'], [0.1, '#34d399'],
        [0.1001, '#fbbf24'], [0.2, '#fbbf24'],
        [0.2001, '#fb923c'], [0.4, '#fb923c'],
        [0.4001, '#ef4444'], [0.6, '#ef4444'],
        [0.6001, '#a855f7'], [0.8, '#a855f7'],
        [0.8001, '#7f1d1d'], [1, '#7f1d1d']
      ],
      zmin: 0,
      zmax: 500,
      xgap: 3,
      ygap: 3,
      hovertemplate: '%{customdata}<extra></extra>',
      colorbar: {
        title: 'AQI',
        tickvals: [25, 75, 150, 250, 350, 450],
        ticktext: ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe']
      }
    }], {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: 'DM Sans, sans-serif', color: '#d0dcda', size: 12 },
      margin: { l: 55, r: 50, t: 12, b: 36 },
      xaxis: {
        title: 'Week of year',
        tickmode: 'array',
        tickvals: Array.from({ length: Math.ceil(weekCount / 4) }, (_, index) => index * 4 + 1),
        gridcolor: 'rgba(0,0,0,0)',
        zeroline: false
      },
      yaxis: { autorange: 'reversed', gridcolor: 'rgba(0,0,0,0)', zeroline: false }
    }, { responsive: true, displayModeBar: false });
  }

  _downloadSeasonalCsv() {
    if (!this.seasonalData?.monthly?.length) return;
    const columns = ['date', 'season', 'observations', 'AQI', 'PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3',
      'Temperature_C', 'Relative_Humidity_pct', 'Wind_Speed_kmh'];
    const escapeCell = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
    const csv = [columns.join(','), ...this.seasonalData.monthly.map((row) =>
      columns.map((column) => escapeCell(row[column])).join(',')
    )].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${this.seasonalData.city.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-monthly-aqi.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  _renderSearch(results) {
    const drop = document.getElementById('search-dropdown-menu');
    if (!drop) return;
    if (!results.length) {
      drop.innerHTML = `<div class="search-item"><div class="search-item-title">No locations found</div></div>`;
    } else {
      drop.innerHTML = results.map(result => `
        <div class="search-item" data-kind="${this._escapeHTML(result.kind)}" data-country-code="${this._escapeHTML(result.country_code || '')}" data-station-id="${this._escapeHTML(result.station_id || '')}">
          <div class="search-item-title">${this._escapeHTML(result.title)}</div>
          <div class="search-item-sub">${this._escapeHTML(result.subtitle)}</div>
        </div>
      `).join('');
      drop.querySelectorAll('.search-item').forEach(item => {
        item.addEventListener('click', async () => {
          drop.classList.remove('active');
          if (item.dataset.kind === 'country') {
            const countrySelect = document.getElementById('country-select');
            if (countrySelect) {
              countrySelect.value = item.dataset.countryCode;
              countrySelect.dispatchEvent(new Event('change'));
            }
            return;
          }
          const station = this.allStations.find(candidate => candidate.station_id === item.dataset.stationId);
          if (station) await this.selectLocation(station);
        });
      });
    }
    drop.classList.add('active');
  }

  async selectLocation(station) {
    const requestId = ++this.locationRequestId;
    this.currentStation = station;
    const coastal = station.is_coastal ? 'true' : 'false';
    const url = `/api/station/overview?lat=${station.lat}&lon=${station.lon}&station_id=${station.station_id || ''}&is_coastal=${coastal}`;
    try {
      const r = await fetch(url);
      const j = await r.json();
      if (requestId === this.locationRequestId && j.status === 'success') {
        this.currentAirQuality = j.air_quality;
        this.currentWeather = j.weather;
        this.currentPrediction = j.model_prediction;
        this.currentMarine = j.marine_intelligence;
        this._updateUI(j);
        this._renderChart('forecast72');
      }
    } catch (e) {
      console.error('[TerraPulse] Location load failed:', e);
    }
  }

  _updateUI(data) {
    const { station: st, air_quality: aq, weather: wx,
      model_prediction: pred, health_advisory: adv,
      marine_intelligence: marine } = data;

    // Location header
    this._setText('telemetry-city-title', st.city || st.name);
    this._setText('telemetry-station-sub',
      `${st.station_name || st.name} • ${st.country} (${st.coordinates.lat.toFixed(2)}°, ${st.coordinates.lon.toFixed(2)}°)`
    );
    const observedCount = Object.keys(aq.observed_measurements || {}).length;
    const provenanceLabel = observedCount === 6
      ? 'OBSERVED · OPENAQ'
      : observedCount > 0
        ? 'PARTIAL · OPENAQ'
        : aq.status === 'FALLBACK' ? 'REFERENCE · DEMO' : 'BASELINE INPUTS';
    this._setText('air-quality-provenance', provenanceLabel);

    // Country focus panel
    this._renderCountryFocus(st.country, st.country_code || this.currentStation?.country_code || 'IN');

    // AQI score
    const score = Math.round(pred.predicted_aqi);
    const cat = pred.category;
    this._setText('aqi-score-number', score);
    this._setStyle('aqi-score-number', 'color', cat.color);
    this._setText('aqi-category-text', cat.name);
    this._setStyle('aqi-category-text', 'color', cat.color);

    // AQI dial progress
    const dialCircle = document.getElementById('aqi-dial-circle');
    if (dialCircle) {
      const maxAQI = 500;
      const progress = Math.min(1, score / maxAQI);
      const circumference = 2 * Math.PI * 50; // r=50
      dialCircle.style.strokeDashoffset = circumference * (1 - progress);
    }

    // Pollutants
    const m = aq.measurements;
    this._setText('val-pm25', m.pm25);
    this._setText('val-pm10', m.pm10);
    this._setText('val-no2', m.no2);
    this._setText('val-co', m.co);
    this._setText('val-so2', m.so2);
    this._setText('val-o3', m.o3);

    // Weather
    this._setText('val-temp', `${wx.temperature_c}°C`);
    this._setText('val-humidity', `${wx.relative_humidity_pct}%`);
    this._setText('val-wind', `${wx.wind_speed_kmh} km/h`);

    // Advisory
    this._setText('advisory-headline', `Guidance: ${adv.status}`);
    this._setText('advisory-summary', adv.general_population_guidance);
    const bul = document.getElementById('advisory-bullets');
    if (bul) bul.innerHTML = adv.recommended_actions.map(a => `<li>${a}</li>`).join('');

    // Marine
    if (marine) {
      const phys = marine.physical_oceanography;
      const bio = marine.biogeochemical_indicators;
      const rec = marine.recreational_guidance;

      this._setText('val-sst', `${phys.sea_surface_temperature_c}°C`);
      this._setText('val-salinity', `${bio.salinity_psu} PSU`);
      this._setText('val-do', `${bio.dissolved_oxygen_mgl} mg/L`);
      this._setText('val-ph', `${bio.ocean_ph}`);
      this._setText('val-chlorophyll', `${bio.chlorophyll_a_mgm3} mg/m³`);
      this._setText('val-recreational-status', rec.status);
      this._setStyle('val-recreational-status', 'color', rec.indicator_color);

      // Mini metrics in ocean story card
      this._setText('mini-sst', `${phys.sea_surface_temperature_c}°C`);
      this._setText('mini-ph', `${bio.ocean_ph}`);
      this._setText('mini-do', `${bio.dissolved_oxygen_mgl} mg/L`);
      this._setText('mini-sal', `${bio.salinity_psu} PSU`);
    }
  }

  _renderCountryFocus(countryName, code) {
    const countryLabel = document.getElementById('focus-country-name');
    const aqiEl = document.getElementById('focus-aqi-score');
    const tagEl = document.getElementById('focus-country-tag');
    const tempEl = document.getElementById('focus-temp');
    const humidityEl = document.getElementById('focus-humidity');
    const windEl = document.getElementById('focus-wind');
    const listEl = document.getElementById('country-stations-list');
    if (!countryLabel || !aqiEl || !listEl) return;

    const countryStations = this.allStations.filter(s => (s.country_code || '').toUpperCase() === (code || '').toUpperCase());
    const localityStations = this.selectedLocality
      ? countryStations.filter(station => station.locality === this.selectedLocality)
      : countryStations;

    const activeCountryName = countryName || (countryStations[0]?.country) || 'Global';
    countryLabel.textContent = activeCountryName;

    const activeScore = this.currentPrediction?.predicted_aqi ? Math.round(this.currentPrediction.predicted_aqi) : '--';
    const activeCategory = this.currentPrediction?.category?.name || 'Awaiting station';
    const weatherTemp = this.currentWeather?.temperature_c;
    const weatherHumidity = this.currentWeather?.relative_humidity_pct;
    const weatherWind = this.currentWeather?.wind_speed_kmh;

    aqiEl.textContent = String(activeScore);
    tagEl.textContent = activeCategory;
    tagEl.style.color = this.currentPrediction?.category?.color || '#94a3b8';
    tagEl.style.borderColor = (this.currentPrediction?.category?.color || '#94a3b8') + '66';
    tempEl.textContent = Number.isFinite(weatherTemp) ? `${weatherTemp.toFixed(1)}°C` : '--';
    humidityEl.textContent = Number.isFinite(weatherHumidity) ? `${weatherHumidity}%` : '--';
    windEl.textContent = Number.isFinite(weatherWind) ? `${weatherWind.toFixed(1)} km/h` : '--';

    const qualityNote = document.getElementById('focus-data-note');
    if (qualityNote) {
      const observedCount = Object.keys(this.currentAirQuality?.observed_measurements || {}).length;
      const missingCount = this.currentAirQuality?.missing_parameters?.length || 0;
      const staleCount = this.currentAirQuality?.stale_parameters?.length || 0;
      qualityNote.textContent = this.currentAirQuality
        ? `OpenAQ pollutants observed: ${observedCount}/6${missingCount ? ` · ${missingCount} baseline inputs used` : ''}${staleCount ? ` · ${staleCount} stale readings ignored` : ''} · Weather: ${this.currentWeather?.provider || 'unavailable'}`
        : 'Select a station to load OpenAQ readings and Open-Meteo weather.';
    }

    const sourceStations = localityStations.slice(0, this.stationDisplayLimit);
    const resultsMeta = document.getElementById('station-results-meta');
    if (resultsMeta && !resultsMeta.textContent.startsWith('Loading') && !resultsMeta.textContent.includes('unavailable')) {
      const localityLabel = this.selectedLocality ? ` · ${this.selectedLocality}` : '';
      resultsMeta.textContent = `${this.allStations.length} loaded locations${localityLabel}`;
    }
    const loadMore = document.getElementById('load-more-stations');
    const hasMoreLoaded = localityStations.length > this.stationDisplayLimit;
    const hasMorePages = this.stationTotal > this.allStations.length || String(this.stationTotal).startsWith('>');
    if (loadMore) {
      loadMore.hidden = !hasMoreLoaded && !hasMorePages;
      loadMore.textContent = hasMoreLoaded ? 'Show more stations' : 'Load next station page';
    }
    listEl.innerHTML = sourceStations.map((station) => {
      const isActive = this.currentStation && this.currentStation.station_id === station.station_id;
      const lastUpdated = station.datetime_last ? new Date(station.datetime_last).toLocaleDateString() : 'No timestamp';
      const stationStatus = isActive && this.currentPrediction
        ? `AQI ${Math.round(this.currentPrediction.predicted_aqi)}`
        : (station.datetime_last ? `Updated ${lastUpdated}` : 'No recent data');
      return `
        <div class="station-card ${isActive ? 'active' : ''}" data-station-id="${this._escapeHTML(station.station_id || '')}">
          <div class="station-card-header">
            <span class="station-name">${this._escapeHTML(station.city || station.name)}</span>
            <span class="station-aqi">${this._escapeHTML(stationStatus)}</span>
          </div>
          <div class="station-meta">
            <span>${this._escapeHTML(station.station_name || station.name)}</span>
            <span>${this._escapeHTML(station.locality || 'State not supplied')}</span>
          </div>
        </div>
      `;
    }).join('');
    if (!sourceStations.length) {
      listEl.innerHTML = '<div class="station-empty">No locations are available for this locality.</div>';
    }
  }

  /* ── Chart Rendering ── */
  async _renderChart(view) {
    const container = document.getElementById('plotly-timeline-chart');
    if (!container || !window.Plotly || !this.currentStation) return;

    container.style.height = view === 'validation' ? 'auto' : '480px';
    const { lat, lon, station_id } = this.currentStation;
    const base = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(4,10,26,0.60)',
      font: { family: 'Inter', color: '#94a3b8', size: 12 },
      margin: { l: 55, r: 45, t: 20, b: 50 },
      legend: { orientation: 'h', y: 1.12, x: 0.05, bgcolor: 'rgba(0,0,0,0)' },
      xaxis: { gridcolor: 'rgba(255,255,255,0.07)', linecolor: 'rgba(255,255,255,0.1)', zerolinecolor: 'rgba(255,255,255,0.07)' },
      yaxis: { gridcolor: 'rgba(255,255,255,0.07)', linecolor: 'rgba(255,255,255,0.1)' }
    };
    const cfg = { responsive: true, displayModeBar: false };

    try {
      if (view === 'forecast72') {
        const resp = await fetch(`/api/aqi/timeline-forecast?lat=${lat}&lon=${lon}&station_id=${station_id || ''}&hours=72`);
        const json = await resp.json();
        const tl = json.timeline || [];
        const times = tl.map(t => t.time);
        const aqiVals = tl.map(t => t.predicted_aqi);
        const pm25Vals = tl.map(t => t.estimated_pm25);
        const temps = tl.map(t => t.weather_inputs.temperature_c);
        Plotly.newPlot(container, [
          { x: times, y: aqiVals, name: 'Estimated AQI', mode: 'lines+markers', line: { color: '#00e5ff', width: 3 }, marker: { size: 5 } },
          { x: times, y: pm25Vals, name: 'Estimated PM₂.₅ (µg/m³)', mode: 'lines', line: { color: '#f59e0b', width: 2, dash: 'dot' } },
          { x: times, y: temps, name: 'Temperature (°C)', mode: 'lines', yaxis: 'y2', line: { color: '#38bdf8', width: 2 } }
        ], { ...base, yaxis2: { title: 'Temp (°C)', overlaying: 'y', side: 'right', showgrid: false }, xaxis: { ...base.xaxis, title: 'Timeline (72h)' }, yaxis: { ...base.yaxis, title: 'AQI / PM₂.₅' } }, cfg);

      } else if (view === 'pollutants') {
        const resp = await fetch(`/api/air-quality/history?lat=${lat}&lon=${lon}&station_id=${station_id || ''}&hours=24`);
        const json = await resp.json();
        const tl = json.timeline || [];
        const times = tl.map(t => t.timestamp);
        Plotly.newPlot(container, [
          { x: times, y: tl.map(t => t.pm25), name: 'PM₂.₅', mode: 'lines', line: { color: '#ef4444', width: 2.5 } },
          { x: times, y: tl.map(t => t.pm10), name: 'PM₁₀', mode: 'lines', line: { color: '#f97316', width: 2.5 } },
          { x: times, y: tl.map(t => t.no2), name: 'NO₂', mode: 'lines', line: { color: '#38bdf8', width: 2 } },
          { x: times, y: tl.map(t => t.o3), name: 'O₃', mode: 'lines', line: { color: '#10b981', width: 2 } }
        ], { ...base, yaxis: { ...base.yaxis, title: 'Concentration (µg/m³)' } }, cfg);

      } else if (view === 'validation') {
        const response = await fetch('/api/model/metadata');
        const result = await response.json();
        if (!response.ok || result.status !== 'success') {
          throw new Error(result.message || 'Estimate accuracy details are unavailable.');
        }
        const metrics = result.data?.metrics || {};
        const meanError = Number(metrics.mae);
        const testSamples = Number(result.data?.test_samples);
        if (!Number.isFinite(meanError) || !Number.isFinite(testSamples)) {
          throw new Error('Estimate accuracy details are incomplete.');
        }
        container.innerHTML =
          `<section class="model-accuracy" aria-labelledby="model-accuracy-title">` +
          `<h3 id="model-accuracy-title">How estimates were checked</h3>` +
          `<p>The AQI estimator was tested using ${testSamples.toLocaleString()} historical records it had not trained on.</p>` +
          `<p>On those records, estimates were typically about <strong>${meanError.toFixed(1)} AQI points</strong> away from the recorded AQI.</p>` +
          `<p class="model-accuracy-note">This describes past test results; it does not guarantee the accuracy of every estimate or forecast.</p>` +
          `</section>`;

      } else if (view === 'marine') {
        const resp = await fetch(`/api/marine/history?lat=${lat}&lon=${lon}&days=7`);
        const json = await resp.json();
        const tl = json.timeline || [];
        const dates = tl.map(t => t.date);
        Plotly.newPlot(container, [
          { x: dates, y: tl.map(t => t.sea_surface_temp_c), name: 'SST (°C)', mode: 'lines', line: { color: '#0ea5e9', width: 2.5 } },
          { x: dates, y: tl.map(t => t.dissolved_oxygen_mgl), name: 'DO (mg/L)', mode: 'lines', line: { color: '#38bdf8', width: 2 } },
          { x: dates, y: tl.map(t => t.salinity_psu), name: 'Salinity (PSU)', mode: 'lines', yaxis: 'y2', line: { color: '#10b981', width: 2, dash: 'dot' } }
        ], { ...base, yaxis2: { title: 'Salinity (PSU)', overlaying: 'y', side: 'right', showgrid: false }, yaxis: { ...base.yaxis, title: 'Temp / DO' } }, cfg);
      }
    } catch (e) {
      console.error('[TerraPulse] Chart error:', e);
    }
  }

  /* ── ML Inference Simulator ── */
  _initSimulator() {
    const sliders = ['sim-pm25', 'sim-pm10', 'sim-no2', 'sim-co', 'sim-temp', 'sim-wind'];
    const run = async () => {
      const pm25 = parseFloat(document.getElementById('sim-pm25')?.value || 35);
      const pm10 = parseFloat(document.getElementById('sim-pm10')?.value || 65);
      const no2 = parseFloat(document.getElementById('sim-no2')?.value || 25);
      const co = parseFloat(document.getElementById('sim-co')?.value || 0.6);
      const temp = parseFloat(document.getElementById('sim-temp')?.value || 24);
      const wind = parseFloat(document.getElementById('sim-wind')?.value || 12);

      this._setText('lbl-sim-pm25', `${pm25} µg/m³`);
      this._setText('lbl-sim-pm10', `${pm10} µg/m³`);
      this._setText('lbl-sim-no2', `${no2} µg/m³`);
      this._setText('lbl-sim-co', `${co} mg/m³`);
      this._setText('lbl-sim-temp', `${temp} °C`);
      this._setText('lbl-sim-wind', `${wind} km/h`);

      try {
        const r = await fetch('/api/aqi/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pm25, pm10, no2, co, so2: 8.0, o3: 40.0,
            temperature_c: temp, relative_humidity_pct: 60, wind_speed_kmh: wind
          })
        });
        const j = await r.json();
        if (j.status === 'success') {
          const d = j.data;
          this._setText('sim-result-aqi', d.predicted_aqi);
          this._setText('sim-result-cat', d.category.name);
          this._setStyle('sim-result-cat', 'color', d.category.color);
          this._setText('sim-result-dominant', `Largest influence: ${d.dominant_pollutant}`);
        }
      } catch { }
    };

    sliders.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', run);
    });
    run();
  }

  /* ── Helpers ── */
  _escapeHTML(value) {
    return String(value ?? '').replace(/[&<>"']/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[character]);
  }

  _setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
  _setStyle(id, prop, val) { const el = document.getElementById(id); if (el) el.style[prop] = val; }
}

/* ─────────────────────────────────────────────────────────────────
   BOOT
   ───────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const steering = document.getElementById('scroll-steering');
  const steeringWheel = steering?.querySelector('svg');

  if (steering && steeringWheel) {
    steering.addEventListener('click', () => {
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const nextScroll = Math.min(maxScroll, window.scrollY + window.innerHeight * 0.78);
      window.scrollTo({ top: nextScroll, behavior: 'smooth' });
    });
  }

  window.app = new TerraPulseApp();
});
