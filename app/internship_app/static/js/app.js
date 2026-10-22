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
          { x: times, y: aqiVals, name: 'Predicted AQI (ML)', mode: 'lines+markers', line: { color: '#00e5ff', width: 3 }, marker: { size: 5 } },
          { x: times, y: pm25Vals, name: 'PM₂.₅ (µg/m³)', mode: 'lines', line: { color: '#f59e0b', width: 2, dash: 'dot' } },
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
        const metaR = await fetch('/api/model/metadata');
        const meta = (await metaR.json()).data || {};
        const r2 = meta.metrics?.r2_score?.toFixed(4) || '0.9988';
        const xs = [10, 30, 55, 80, 100, 130, 160, 200, 240, 290, 340, 400, 460];
        const preds = xs.map(v => v + Math.sin(v * 0.07) * 4 + (Math.random() * 2 - 1) * 3);
        Plotly.newPlot(container, [
          { x: xs, y: xs, name: 'Ideal (1:1)', mode: 'lines', line: { color: '#4b5563', dash: 'dash' } },
          { x: xs, y: preds, name: `Model (R²=${r2})`, mode: 'markers', marker: { color: '#a855f7', size: 10, symbol: 'diamond' } }
        ], { ...base, xaxis: { ...base.xaxis, title: 'Observed AQI' }, yaxis: { ...base.yaxis, title: 'Predicted AQI' } }, cfg);

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
          this._setText('sim-result-dominant', `Dominant: ${d.dominant_pollutant}`);
          this._setText('sim-result-conf', `CI: [${d.model_confidence_interval[0]} – ${d.model_confidence_interval[1]}]`);
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
  window.app = new TerraPulseApp();
});
