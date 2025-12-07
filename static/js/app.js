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
    });
});

// Load today's mantras
async function loadToday() {
    const response = await fetch('/api/today');
    const data = await response.json();
    
    document.getElementById('current-date').textContent = new Date(data.date).toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
    
    document.getElementById('nakshatra-badge').textContent = `Nakshatra: ${data.nakshatra}`;
    document.getElementById('tithi-badge').textContent = `Tithi: ${data.tithi}`;
    document.getElementById('day-badge').textContent = `${data.day} | ${data.current_time}`;
    
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
    const today = new Date().toISOString().split('T')[0];
    const response = await fetch(`/api/astro/${today}`);
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
    displayMantras(filtered);
});

// Load Panchang data
async function loadPanchang() {
    const today = new Date().toISOString().split('T')[0];
    try {
        const response = await fetch(`/api/panchang/${today}`);
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

// Initialize
loadToday();
loadPanchang();

// Note: The backend currently uses Vedic time by default (USE_VEDIC_TIME = True in app.py)
// This toggle is informational - showing users which system is being used
