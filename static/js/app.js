let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let allMantrasData = [];

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
        
        if (tab.dataset.tab === 'calendar') loadCalendar();
        if (tab.dataset.tab === 'astro') loadAstrology();
        if (tab.dataset.tab === 'library') loadAllMantras();
        if (tab.dataset.tab === 'manifest') loadManifestation();
    });
});

// Load today's mantras
async function loadToday() {
    const now = new Date();
    // Send local date and time separately for accuracy
    const localDate = now.toLocaleDateString('en-CA'); // YYYY-MM-DD format
    const localTime = now.toLocaleTimeString('en-US', { hour12: false }); // HH:MM:SS format
    const dayName = now.toLocaleDateString('en-US', { weekday: 'long' });
    const response = await fetch(`/api/today?local_date=${localDate}&local_time=${localTime}&day_name=${dayName}`);
    const data = await response.json();
    
    document.getElementById('current-date').textContent = new Date(data.date).toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
    
    document.getElementById('nakshatra-badge').textContent = `Nakshatra: ${data.nakshatra}`;
    document.getElementById('tithi-badge').textContent = `Tithi: ${data.tithi}`;
    
    // Display client's actual time
    const updateTime = () => {
        const now = new Date();
        const displayTime = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
        document.getElementById('day-badge').textContent = `${data.day} | ${displayTime}`;
    };
    updateTime();
    // Update time every second
    setInterval(updateTime, 1000);
    
    // Display location
    if (data.location) {
        document.getElementById('location-info').innerHTML = `📍 ${data.location}`;
    }
    
    // Display festival if today is special
    if (data.festival) {
        const festivalBanner = document.getElementById('festival-banner');
        festivalBanner.style.display = 'block';
        festivalBanner.innerHTML = `🎉 Today is ${data.festival}! 🎉`;
    }
    
    // Display moon phase
    if (data.moon_phase) {
        const moon = data.moon_phase;
        document.getElementById('moon-badge').innerHTML = `
            ${moon.emoji} ${moon.name}<br>
            <small>${moon.vedic}</small>
        `;
    }
    
    // Update sunrise/sunset times from API
    if (data.sunrise && data.sunset) {
        document.getElementById('sun-times').innerHTML = `
            <span class="sun-time">🌅 Sunrise: ${data.sunrise}</span>
            <span class="sun-time">🌇 Sunset: ${data.sunset}</span>
        `;
    }
    
    // Display strongest planet
    if (data.strongest_planet) {
        document.getElementById('strongest-planet').innerHTML = `
            ⭐ Strongest Planet Today: <strong>${data.strongest_planet}</strong> 
            (${data.planet_strength}% strength)
        `;
    }
    
    const container = document.getElementById('today-mantras');
    container.innerHTML = data.mantras.map(m => createMantraCard(m)).join('');
}

function createMantraCard(mantra) {
    const categories = mantra.category.split(',');
    return `
        <div class="mantra-card">
            <h3>${mantra.name}</h3>
            <div class="sanskrit">${mantra.sanskrit}</div>
            <div class="transliteration">${mantra.transliteration}</div>
            <div class="meaning">${mantra.meaning}</div>
            <div class="tags">
                <span class="tag">🙏 ${mantra.deity}</span>
                ${categories.map(c => `<span class="tag">${c.trim()}</span>`).join('')}
            </div>
            <div style="margin-top: 15px; color: #666; font-size: 0.9em;">
                <strong>Benefits:</strong> ${mantra.benefits}
            </div>
            <button class="chant-counter-btn" onclick="openCounter('${mantra.name.replace(/'/g, "\\'")}')">📿 Start Chanting (108x)</button>
        </div>
    `;
}

// Calendar
async function loadCalendar() {
    const response = await fetch(`/api/calendar/${currentYear}/${currentMonth + 1}`);
    const days = await response.json();
    
    document.getElementById('calendar-month').textContent = 
        new Date(currentYear, currentMonth).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    
    const grid = document.getElementById('calendar-grid');
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    
    let html = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        .map(d => `<div style="font-weight: bold; text-align: center; padding: 10px;">${d}</div>`).join('');
    
    for (let i = 0; i < firstDay; i++) {
        html += '<div></div>';
    }
    
    days.forEach(day => {
        let festivalClass = day.festival ? 'festival-day' : '';
        let moonClass = day.is_purnima ? 'purnima-day' : (day.is_amavasya ? 'amavasya-day' : '');
        let festivalBadge = day.festival ? `<div class="festival-badge">🎉</div>` : '';
        let moonBadge = day.moon_phase ? `<div class="moon-icon">${day.moon_phase}</div>` : '';
        
        html += `
            <div class="calendar-day ${festivalClass} ${moonClass}" 
                 onclick="selectDay('${day.date}', '${day.nakshatra}', '${day.tithi}', '${day.festival || ''}')">
                ${festivalBadge}
                ${moonBadge}
                <div class="day-number">${day.day}</div>
                <div class="day-nakshatra">${day.nakshatra}</div>
            </div>
        `;
    });
    
    grid.innerHTML = html;
}

function selectDay(date, nakshatra, tithi, festival) {
    document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    
    let festivalInfo = festival ? `<p style="color: #ff6b35; font-weight: bold;">🎉 ${festival}</p>` : '';
    
    document.getElementById('selected-day-info').innerHTML = `
        <h3>${new Date(date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</h3>
        ${festivalInfo}
        <p><strong>Nakshatra:</strong> ${nakshatra}</p>
        <p><strong>Tithi:</strong> ${tithi}</p>
        <p style="margin-top: 10px;">Recommended mantras for this day are based on the nakshatra and planetary positions.</p>
    `;
}

document.getElementById('prev-month').addEventListener('click', () => {
    currentMonth--;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    }
    loadCalendar();
});

document.getElementById('next-month').addEventListener('click', () => {
    currentMonth++;
    if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    loadCalendar();
});

// Astrology
async function loadAstrology() {
    const now = new Date();
    const today = now.toISOString().split('T')[0];
    const clientTime = now.toISOString();
    const response = await fetch(`/api/astro/${today}?client_time=${encodeURIComponent(clientTime)}`);
    const data = await response.json();
    
    // Display auspicious time
    if (data.auspicious_time) {
        document.getElementById('auspicious-time').innerHTML = `
            ⏰ <strong>Auspicious Time:</strong> ${data.auspicious_time}
        `;
    }
    
    // Display recommendation
    if (data.recommendation) {
        document.getElementById('day-recommendation').innerHTML = `
            💡 <strong>Today's Insight:</strong><br>${data.recommendation}
        `;
    }
    
    // Find strongest planet
    const strongest = Object.entries(data.planets).reduce((a, b) => 
        a[1].strength > b[1].strength ? a : b
    );
    
    const container = document.getElementById('planet-positions');
    container.innerHTML = Object.entries(data.planets).map(([planet, info]) => `
        <div class="planet-card ${planet === strongest[0] ? 'strong' : ''}">
            <h3>${getPlanetEmoji(planet)} ${planet}</h3>
            <div class="planet-sign">${info.sign}</div>
            <div>Position: ${info.degree.toFixed(2)}°</div>
            <div class="strength-bar">
                <div class="strength-fill" style="width: ${info.strength}%"></div>
            </div>
            <div style="margin-top: 5px;">Strength: ${info.strength}%</div>
            ${planet === strongest[0] ? '<div style="margin-top: 10px;">⭐ Strongest Today</div>' : ''}
        </div>
    `).join('');
}

function getPlanetEmoji(planet) {
    const emojis = {
        'Sun': '☀️', 'Moon': '🌙', 'Mars': '♂️', 'Mercury': '☿️',
        'Jupiter': '♃', 'Venus': '♀️', 'Saturn': '♄'
    };
    return emojis[planet] || '⭐';
}

// Mantra Library
async function loadAllMantras() {
    if (allMantrasData.length === 0) {
        const response = await fetch('/api/mantras');
        allMantrasData = await response.json();
    }
    displayMantras(allMantrasData);
}

function displayMantras(mantras) {
    const container = document.getElementById('all-mantras');
    container.innerHTML = mantras.map(m => createMantraCard(m)).join('');
}

document.getElementById('search').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = allMantrasData.filter(m => 
        m.name.toLowerCase().includes(query) ||
        m.deity.toLowerCase().includes(query) ||
        m.category.toLowerCase().includes(query) ||
        m.benefits.toLowerCase().includes(query)
    );
    
    if (filtered.length === 0 && query.length > 0) {
        // Show helpful message when no results
        const container = document.getElementById('all-mantras');
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <h3>No results found for "${query}"</h3>
                <p style="margin: 20px 0;">We currently have mantras for:</p>
                <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 20px;">
                    <span style="background: #667eea; color: white; padding: 8px 16px; border-radius: 20px;">Ganesha</span>
                    <span style="background: #667eea; color: white; padding: 8px 16px; border-radius: 20px;">Hanuman</span>
                    <span style="background: #667eea; color: white; padding: 8px 16px; border-radius: 20px;">Shiva</span>
                    <span style="background: #667eea; color: white; padding: 8px 16px; border-radius: 20px;">Lakshmi</span>
                    <span style="background: #667eea; color: white; padding: 8px 16px; border-radius: 20px;">Saraswati</span>
                    <span style="background: #667eea; color: white; padding: 8px 16px; border-radius: 20px;">Durga</span>
                    <span style="background: #667eea; color: white; padding: 8px 16px; border-radius: 20px;">Vishnu</span>
                </div>
                <p style="margin-top: 20px; font-size: 0.9em;">Try searching for deity names, benefits (wealth, health, peace), or categories (Vedic, planetary)</p>
            </div>
        `;
    } else {
        displayMantras(filtered);
    }
});

// Load Panchang data
async function loadPanchang() {
    const now = new Date();
    const today = now.toISOString().split('T')[0];
    const clientTime = now.toISOString();
    try {
        const response = await fetch(`/api/panchang/${today}?client_time=${encodeURIComponent(clientTime)}`);
        const data = await response.json();
        
        document.getElementById('ai-recommendation').innerHTML = `
            📅 <strong>Panchang:</strong> Yoga: ${data.yoga} | Karana: ${data.karana}
        `;
    } catch (error) {
        console.log('Panchang data not available');
    }
}

const timeToggle = document.getElementById('time-toggle');
let useVedicTime = true;

// Time system toggle
timeToggle.addEventListener('click', () => {
    useVedicTime = !useVedicTime;
    const timeInfoDiv = document.getElementById('time-info');
    
    if (useVedicTime) {
        timeToggle.textContent = '🌅 Vedic Time';
        timeToggle.classList.add('vedic');
        timeInfoDiv.innerHTML = '<small>📖 Day starts at sunrise (Vedic tradition)</small>';
    } else {
        timeToggle.textContent = '🕛 Western Time';
        timeToggle.classList.remove('vedic');
        timeInfoDiv.innerHTML = '<small>🕰️ Day starts at midnight (Western system)</small>';
    }
});

// Initialize
timeToggle.classList.add('vedic');

// Show explanation on hover
timeToggle.addEventListener('mouseenter', () => {
    const timeInfoDiv = document.getElementById('time-info');
    if (useVedicTime) {
        timeInfoDiv.innerHTML = '<small>🌅 Before sunrise = previous day | After sunrise = current day</small>';
    } else {
        timeInfoDiv.innerHTML = '<small>🕛 After midnight = current day (standard calendar)</small>';
    }
});

timeToggle.addEventListener('mouseleave', () => {
    const timeInfoDiv = document.getElementById('time-info');
    if (useVedicTime) {
        timeInfoDiv.innerHTML = '<small>📖 Day starts at sunrise (Vedic tradition)</small>';
    } else {
        timeInfoDiv.innerHTML = '<small>🕰️ Day starts at midnight (Western system)</small>';
    }
});

// Manifestation Section
async function loadManifestation() {
    const response = await fetch('/api/manifestation');
    const data = await response.json();
    
    // Magic Time Alert
    if (data.is_magic_time) {
        document.getElementById('magic-time').innerHTML = `
            ✨ MAGIC TIME ALERT! ✨<br>
            ${data.current_time} - ${data.magic_message}
        `;
    } else {
        document.getElementById('magic-time').innerHTML = `
            🕰️ Next Magic Time: ${data.next_magic_time}
        `;
    }
    
    // Angel Numbers
    document.getElementById('angel-numbers').innerHTML = data.angel_numbers.map(num => `
        <div class="magic-number" title="${num.meaning}">${num.number}</div>
    `).join('');
    
    // Power Hours
    document.getElementById('power-hours').innerHTML = data.power_hours.map(hour => `
        <div class="power-hour-item">
            <strong>${hour.time}</strong><br>
            ${hour.activity}
        </div>
    `).join('');
    
    // Moon Manifestation
    document.getElementById('moon-manifest').innerHTML = `
        <div style="font-size: 3em; margin: 15px 0;">${data.moon_phase.emoji}</div>
        <h4 style="margin: 10px 0;">${data.moon_phase.name}</h4>
        <p style="line-height: 1.6;">${data.moon_phase.manifestation}</p>
    `;
    
    // Daily Affirmation
    document.getElementById('daily-affirmation').innerHTML = `
        <p style="font-size: 1.2em; line-height: 1.8; font-style: italic;">
            "${data.affirmation}"
        </p>
    `;
    
    // Ritual Steps
    document.getElementById('ritual-steps').innerHTML = data.ritual.map((step, i) => `
        <div class="ritual-step">
            <strong>Step ${i + 1}:</strong> ${step}
        </div>
    `).join('');
}

// Mantra Counter
let counterValue = 0;
let currentMantra = '';

function openCounter(mantraName) {
    currentMantra = mantraName;
    counterValue = 0;
    document.getElementById('counter-mantra-name').textContent = mantraName;
    document.getElementById('counter-number').textContent = '0';
    document.getElementById('counter-progress').style.width = '0%';
    document.getElementById('counter-modal').style.display = 'flex';
    document.getElementById('counter-btn').disabled = false;
}

function incrementCounter() {
    if (counterValue < 108) {
        counterValue++;
        document.getElementById('counter-number').textContent = counterValue;
        const progress = (counterValue / 108) * 100;
        document.getElementById('counter-progress').style.width = progress + '%';
        
        // Vibration feedback on mobile
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        // Celebration at 108
        if (counterValue === 108) {
            document.getElementById('counter-btn').disabled = true;
            document.getElementById('counter-number').style.animation = 'celebrate 1s ease-in-out';
            setTimeout(() => {
                alert('🎉 Congratulations! You completed 108 chants! 🙏');
            }, 500);
        }
    }
}

function resetCounter() {
    counterValue = 0;
    document.getElementById('counter-number').textContent = '0';
    document.getElementById('counter-progress').style.width = '0%';
    document.getElementById('counter-btn').disabled = false;
    document.getElementById('counter-number').style.animation = '';
}

// Close modal
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('counter-modal');
    const closeBtn = document.querySelector('.counter-close');
    
    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (e) => {
        if (e.target === modal) modal.style.display = 'none';
    };
    
    // Keyboard support
    document.addEventListener('keydown', (e) => {
        if (modal.style.display === 'flex') {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                incrementCounter();
            } else if (e.key === 'Escape') {
                modal.style.display = 'none';
            }
        }
    });
});

// Initialize
loadToday();
loadPanchang();

// Check for magic time every minute
setInterval(() => {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const time = `${hours}:${minutes}`;
    
    const magicTimes = ['11:11', '22:22', '00:00', '12:12', '13:13', '14:14', '15:15', '21:21', '23:23'];
    
    if (magicTimes.includes(time)) {
        // Reload manifestation if on that tab
        const manifestTab = document.getElementById('manifest');
        if (manifestTab && manifestTab.classList.contains('active')) {
            loadManifestation();
        }
    }
}, 60000);

// Note: The backend currently uses Vedic time by default (USE_VEDIC_TIME = True in app.py)
// This toggle is informational - showing users which system is being used
