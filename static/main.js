// Global variables
let map;
let eventMarkers = [];
let currentFilters = {
    types: ['maritime', 'climate', 'supply-chain'],
    severities: ['critical', 'high', 'medium', 'low'],
    region: '',
    search: ''
};
let eventData = [];
let geoData = [];
let eventsChart = null;
let regionsChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    loadInitialData();
    setupEventListeners();
    updateSelectAllButtons(); // Initialize select all button states
    startAutoRefresh();
    initializeCharts();
    configureMarkdown();
});

// Initialize the Leaflet map
function initializeMap() {
    map = L.map('world-map', {
        attributionControl: false,
        center: [30, 0],
        zoom: 2,
        zoomControl: true,
        worldCopyJump: true
    });

    // Store initial view for reset functionality
    map.initialCenter = [30, 0];
    map.initialZoom = 2;

    // Add dark theme tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    // Add custom styling
    map.getContainer().style.background = '#1a2332';
}

// Load initial data from API
async function loadInitialData() {
    showLoading();
    
    try {
        // Load events and geo data in parallel
        const [eventsResponse, geoResponse] = await Promise.all([
            fetch('/api/events'),
            fetch('/api/geo-data')
        ]);

        if (eventsResponse.ok) {
            const eventsData = await eventsResponse.json();
            eventData = eventsData.events || [];
            
            // Generate dynamic event type filters
            generateEventTypeFilters();
            
            updateEventList();
            updateMapMarkers();
            updateHeaderStats();
            updateMetrics();
            updateCharts();
        }

        if (geoResponse.ok) {
            const geoDataResponse = await geoResponse.json();
            geoData = geoDataResponse.features || [];
        }

    } catch (error) {
        console.error('Error loading initial data:', error);
        showNotification('Error loading data. Please check your connection.', 'error');
    } finally {
        hideLoading();
    }
}

// Setup event listeners
function setupEventListeners() {
    // View tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const viewName = this.dataset.view;
            switchView(viewName);
            
            // Update active tab
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Event type filters are now set up dynamically in generateEventTypeFilters()

    // Severity filters
    document.querySelectorAll('[id^="severity-"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const severity = this.id.replace('severity-', '');
            if (this.checked) {
                if (!currentFilters.severities.includes(severity)) {
                    currentFilters.severities.push(severity);
                }
            } else {
                currentFilters.severities = currentFilters.severities.filter(s => s !== severity);
            }
            applyFilters();
            updateSelectAllButtons();
        });
    });

    // Select All buttons
    const selectAllTypesBtn = document.getElementById('select-all-types');
    const selectAllSeverityBtn = document.getElementById('select-all-severity');

    if (selectAllTypesBtn) {
        selectAllTypesBtn.addEventListener('click', function() {
            const filterContainer = document.getElementById('event-type-filters');
            if (!filterContainer) return;
            
            const typeCheckboxes = filterContainer.querySelectorAll('input[type="checkbox"]');
            const allChecked = Array.from(typeCheckboxes).every(cb => cb.checked);
            
            typeCheckboxes.forEach(checkbox => {
                checkbox.checked = !allChecked;
                const filterType = checkbox.id.replace('filter-', '');
                if (!allChecked) {
                    if (!currentFilters.types.includes(filterType)) {
                        currentFilters.types.push(filterType);
                    }
                } else {
                    currentFilters.types = currentFilters.types.filter(t => t !== filterType);
                }
            });
            
            applyFilters();
            updateSelectAllButtons();
        });
    }

    if (selectAllSeverityBtn) {
        selectAllSeverityBtn.addEventListener('click', function() {
            const severityCheckboxes = document.querySelectorAll('[id^="severity-"]');
            const allChecked = Array.from(severityCheckboxes).every(cb => cb.checked);
            
            severityCheckboxes.forEach(checkbox => {
                checkbox.checked = !allChecked;
                const severity = checkbox.id.replace('severity-', '');
                if (!allChecked) {
                    if (!currentFilters.severities.includes(severity)) {
                        currentFilters.severities.push(severity);
                    }
                } else {
                    currentFilters.severities = currentFilters.severities.filter(s => s !== severity);
                }
            });
            
            applyFilters();
            updateSelectAllButtons();
        });
    }

    // Region filter - only if element exists
    const regionFilter = document.getElementById('region-filter');
    if (regionFilter) {
        regionFilter.addEventListener('change', function() {
            currentFilters.region = this.value;
            applyFilters();
        });
    }

    // Events search
    const searchInput = document.getElementById('events-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            currentFilters.search = this.value.toLowerCase();
            applyFilters();
        });
    }

    // Events sort
    const sortSelect = document.getElementById('events-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            updateEventList();
        });
    }

    // Map layer controls
    document.querySelectorAll('.map-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Skip if this is the chat toggle button or reset button
            if (this.id === 'map-chat-toggle' || this.id === 'reset-map-btn') return;
            
            document.querySelectorAll('.map-btn:not(#map-chat-toggle):not(#reset-map-btn)').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            if (this.dataset.layer) {
                switchMapLayer(this.dataset.layer);
            }
        });
    });

    // Reset map button
    const resetMapBtn = document.getElementById('reset-map-btn');
    if (resetMapBtn) {
        resetMapBtn.addEventListener('click', function() {
            resetMapView();
        });
    }

    // File uploads - DISABLED until backend implementation is complete
    // document.getElementById('image-upload').addEventListener('change', handleImageUpload);
    // document.getElementById('audio-upload').addEventListener('change', handleAudioUpload);

    // Chat functionality
    document.getElementById('send-chat').addEventListener('click', sendChatMessage);
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });

    // Quick questions
    document.querySelectorAll('.quick-q-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const question = this.dataset.question;
            document.getElementById('chat-input').value = question;
            sendChatMessage();
        });
    });

    // Refresh intelligence - only if element exists
    const refreshIntelligenceBtn = document.getElementById('refresh-intelligence');
    if (refreshIntelligenceBtn) {
        refreshIntelligenceBtn.addEventListener('click', function() {
            // Since we removed the intelligence summary, this could refresh metrics instead
            updateMetrics();
        });
    }



    // Map chat sidebar functionality
    const mapChatToggle = document.getElementById('map-chat-toggle');
    const mapChatSidebar = document.getElementById('map-chat-sidebar');
    const mapChatClose = document.getElementById('map-chat-close');
    const mapContent = document.querySelector('.map-content');

    if (mapChatToggle) {
        mapChatToggle.addEventListener('click', function() {
            toggleMapChatSidebar();
        });
    }

    if (mapChatClose) {
        mapChatClose.addEventListener('click', function() {
            closeMapChatSidebar();
        });
    }

    // Map chat input functionality
    const mapSendChat = document.getElementById('map-send-chat');
    const mapChatInput = document.getElementById('map-chat-input');

    if (mapSendChat) {
        mapSendChat.addEventListener('click', function() {
            sendMapChatMessage();
        });
    }

    if (mapChatInput) {
        mapChatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMapChatMessage();
            }
        });
    }

    // Map quick questions
    document.querySelectorAll('.map-quick-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const question = this.dataset.question;
            document.getElementById('map-chat-input').value = question;
            sendMapChatMessage();
        });
    });
}

// Switch between views
function switchView(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    
    // Show selected view
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.classList.add('active');
        
        // If switching to map view, resize map
        if (viewName === 'map' && map) {
            setTimeout(() => map.invalidateSize(), 100);
        }
    }
}

// Apply all filters
function applyFilters() {
    updateEventList();
    updateMapMarkers();
    updateMetrics();
    updateCharts();
}

// Update select all button states
function updateSelectAllButtons() {
    // Update event types select all button
    const selectAllTypesBtn = document.getElementById('select-all-types');
    if (selectAllTypesBtn) {
        const filterContainer = document.getElementById('event-type-filters');
        if (filterContainer) {
            const typeCheckboxes = filterContainer.querySelectorAll('input[type="checkbox"]');
            const allChecked = Array.from(typeCheckboxes).every(cb => cb.checked);
            const someChecked = Array.from(typeCheckboxes).some(cb => cb.checked);
            
            if (allChecked) {
                selectAllTypesBtn.textContent = 'Deselect All';
                selectAllTypesBtn.classList.add('deselect');
            } else {
                selectAllTypesBtn.textContent = 'Select All';
                selectAllTypesBtn.classList.remove('deselect');
            }
        }
    }
    
    // Update severity select all button
    const selectAllSeverityBtn = document.getElementById('select-all-severity');
    if (selectAllSeverityBtn) {
        const severityCheckboxes = document.querySelectorAll('[id^="severity-"]');
        const allChecked = Array.from(severityCheckboxes).every(cb => cb.checked);
        const someChecked = Array.from(severityCheckboxes).some(cb => cb.checked);
        
        if (allChecked) {
            selectAllSeverityBtn.textContent = 'Deselect All';
            selectAllSeverityBtn.classList.add('deselect');
        } else {
            selectAllSeverityBtn.textContent = 'Select All';
            selectAllSeverityBtn.classList.remove('deselect');
        }
    }
}

// Get filtered events
function getFilteredEvents() {
    return eventData.filter(event => {
        // Type filter
        if (!currentFilters.types.includes(event.category)) {
            return false;
        }
        
        // Severity filter
        if (!currentFilters.severities.includes(event.severity)) {
            return false;
        }
        
        // Region filter
        if (currentFilters.region && !event.location.toLowerCase().includes(currentFilters.region.toLowerCase())) {
            return false;
        }
        
        // Search filter
        if (currentFilters.search) {
            const searchableText = `${event.title} ${event.description} ${event.location}`.toLowerCase();
            if (!searchableText.includes(currentFilters.search)) {
                return false;
            }
        }
        
        return true;
    });
}

// Update event list in the events view
function updateEventList() {
    const eventList = document.getElementById('events-list');
    if (!eventList) return;
    
    let filteredEvents = getFilteredEvents();
    
    // Apply sorting
    const sortBy = document.getElementById('events-sort')?.value || 'newest';
    switch (sortBy) {
        case 'oldest':
            filteredEvents.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            break;
        case 'severity':
            const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
            filteredEvents.sort((a, b) => severityOrder[b.severity] - severityOrder[a.severity]);
            break;
        case 'newest':
        default:
            filteredEvents.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            break;
    }

    if (filteredEvents.length === 0) {
        eventList.innerHTML = '<div class="no-events" style="text-align: center; padding: 2rem; color: #94a3b8;">No events found for current filters.</div>';
        return;
    }

    eventList.innerHTML = filteredEvents.map(event => `
        <div class="event-item">
            <div class="event-content" onclick="focusOnEvent(${event.id})">
                <div class="event-title">${event.title}</div>
                <div class="event-meta">
                    <span>${event.location}</span>
                    <span class="event-severity severity-${event.severity}">${event.severity}</span>
                </div>
                <div class="event-description">${event.description}</div>
                <div class="event-meta">
                    <span>${new Date(event.timestamp).toLocaleString()}</span>
                    <span>${event.category}</span>
                </div>
            </div>
            <div class="event-actions">
                <button class="delete-event-btn" onclick="deleteEvent(${event.id}, event)" title="Delete Event">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Update map markers
function updateMapMarkers() {
    // Clear existing markers
    eventMarkers.forEach(marker => map.removeLayer(marker));
    eventMarkers = [];

    const filteredEvents = getFilteredEvents();

    // Add new markers
    filteredEvents.forEach(event => {
        if (event.lat && event.lon) {
            const severity = event.severity || 'medium';
            const eventType = event.category || 'maritime';
            const color = getEventTypeColor(eventType);
            
            const marker = L.circleMarker([event.lat, event.lon], {
                radius: getSeverityRadius(severity),
                fillColor: color,
                color: '#ffffff',
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.6
            }).addTo(map);

            // Add popup
            marker.bindPopup(`
                <div class="map-popup">
                    <h4>${event.title}</h4>
                    <p><strong>Location:</strong> ${event.location}</p>
                    <p><strong>Severity:</strong> <span class="severity-${severity}">${severity.toUpperCase()}</span></p>
                    <p><strong>Category:</strong> ${event.category}</p>
                    <p>${event.description}</p>
                    <p><small>${new Date(event.timestamp).toLocaleString()}</small></p>
                </div>
            `);

            eventMarkers.push(marker);
        }
    });
}

// Update metrics
function updateMetrics() {
    const filteredEvents = getFilteredEvents();
    const highSeverityEvents = filteredEvents.filter(e => e.severity === 'high' || e.severity === 'critical');
    const activeRegions = new Set(filteredEvents.map(e => e.location)).size;
    
    document.getElementById('total-events').textContent = filteredEvents.length;
    document.getElementById('high-severity').textContent = highSeverityEvents.length;
    document.getElementById('active-regions').textContent = activeRegions;
}

// Initialize charts
function initializeCharts() {
    const eventsCtx = document.getElementById('events-chart');
    const regionsCtx = document.getElementById('regions-chart');
    
    if (eventsCtx && Chart) {
        eventsChart = new Chart(eventsCtx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#dc2626', '#ef4444', '#fbbf24', '#22c55e'],
                    borderColor: '#1a2332',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#e2e8f0', font: { size: 10 } }
                    }
                }
            }
        });
    }
    
    if (regionsCtx && Chart) {
        regionsChart = new Chart(regionsCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Events by Region',
                    data: [],
                    backgroundColor: '#3b82f6',
                    borderColor: '#60a5fa',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { 
                        ticks: { color: '#e2e8f0', font: { size: 8 } },
                        grid: { color: '#374151' }
                    },
                    y: { 
                        ticks: { color: '#e2e8f0', font: { size: 8 } },
                        grid: { color: '#374151' }
                    }
                }
            }
        });
    }
}

// Update charts with current data
function updateCharts() {
    const filteredEvents = getFilteredEvents();
    
    // Update severity chart
    if (eventsChart) {
        const severityCounts = {
            critical: filteredEvents.filter(e => e.severity === 'critical').length,
            high: filteredEvents.filter(e => e.severity === 'high').length,
            medium: filteredEvents.filter(e => e.severity === 'medium').length,
            low: filteredEvents.filter(e => e.severity === 'low').length
        };
        
        eventsChart.data.datasets[0].data = [
            severityCounts.critical,
            severityCounts.high,
            severityCounts.medium,
            severityCounts.low
        ];
        eventsChart.update();
    }
    
    // Update regions chart
    if (regionsChart) {
        const regionCounts = {};
        filteredEvents.forEach(event => {
            const region = event.location.split(',')[0]; // Get first part of location
            regionCounts[region] = (regionCounts[region] || 0) + 1;
        });
        
        const sortedRegions = Object.entries(regionCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 6); // Top 6 regions
        
        regionsChart.data.labels = sortedRegions.map(([region]) => region);
        regionsChart.data.datasets[0].data = sortedRegions.map(([,count]) => count);
        regionsChart.update();
    }
}

// Get color based on event type (category)
function getEventTypeColor(eventType) {
    // Base colors for common types
    const baseColors = {
        'maritime': '#ef4444',      // Red for Maritime/AIS
        'climate': '#f97316',       // Orange for Climate/Food  
        'supply-chain': '#3b82f6',  // Blue for Supply Chain
        'conflict': '#dc2626',      // Dark red for Conflict
        'cyber': '#7c3aed',         // Purple for Cyber
        'terrorism': '#000000',     // Black for Terrorism
        'political': '#059669'      // Green for Political
    };
    
    // If we have a predefined color, use it
    if (baseColors[eventType]) {
        return baseColors[eventType];
    }
    
    // For new event types, generate a consistent color based on the type name
    return generateColorFromString(eventType);
}

function generateColorFromString(str) {
    // Generate a consistent color based on string hash
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Convert hash to HSL for better color distribution
    const hue = Math.abs(hash) % 360;
    const saturation = 60 + (Math.abs(hash) % 40); // 60-100%
    const lightness = 45 + (Math.abs(hash) % 20);  // 45-65%
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function generateEventTypeFilters() {
    // Get all unique event types from current data
    const eventTypes = [...new Set(eventData.map(event => event.category))].sort();
    
    // Initialize filters to include all types
    currentFilters = {
        types: [...eventTypes],
        severities: ['low', 'medium', 'high', 'critical'],
        region: '',
        search: ''
    };
    
    // Get the filter container
    const filterContainer = document.getElementById('event-type-filters');
    if (!filterContainer) return;
    
    // Clear existing filters
    filterContainer.innerHTML = '';
    
    // Generate filters for each event type
    eventTypes.forEach(type => {
        const color = getEventTypeColor(type);
        const displayName = formatEventTypeName(type);
        
        const filterItem = document.createElement('label');
        filterItem.className = 'filter-item';
        filterItem.innerHTML = `
            <input type="checkbox" id="filter-${type}" checked>
            <span class="event-marker" style="background-color: ${color};"></span>
            ${displayName}
        `;
        
        filterContainer.appendChild(filterItem);
        
        // Add event listener to the new checkbox
        const checkbox = filterItem.querySelector('input');
        checkbox.addEventListener('change', function() {
            const filterType = this.id.replace('filter-', '');
            if (this.checked) {
                if (!currentFilters.types.includes(filterType)) {
                    currentFilters.types.push(filterType);
                }
            } else {
                currentFilters.types = currentFilters.types.filter(t => t !== filterType);
            }
            applyFilters();
            updateSelectAllButtons();
        });
    });
}

function formatEventTypeName(type) {
    // Convert kebab-case and snake_case to Title Case
    return type
        .replace(/[-_]/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

// Get color based on severity (kept for reference/other uses)
function getSeverityColor(severity) {
    const colors = {
        low: '#22c55e',
        medium: '#fbbf24',
        high: '#ef4444',
        critical: '#dc2626'
    };
    return colors[severity] || colors.medium;
}

// Get radius based on severity
function getSeverityRadius(severity) {
    const radii = {
        low: 8,
        medium: 12,
        high: 16,
        critical: 20
    };
    return radii[severity] || radii.medium;
}

// Focus on specific event
function focusOnEvent(eventId) {
    // Switch to map view
    switchView('map');
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById('map-tab').classList.add('active');
    
    const event = eventData.find(e => e.id === eventId);
    if (event && event.lat && event.lon) {
        setTimeout(() => {
            map.setView([event.lat, event.lon], 6);
            
            // Find and open the popup for this event
            const marker = eventMarkers.find(m => {
                const latLng = m.getLatLng();
                return Math.abs(latLng.lat - event.lat) < 0.01 && Math.abs(latLng.lng - event.lon) < 0.01;
            });
            
            if (marker) {
                marker.openPopup();
            }
        }, 200);
    }
}

// Delete event function
async function deleteEvent(eventId, clickEvent) {
    // Prevent event bubbling to avoid triggering focusOnEvent
    if (clickEvent) {
        clickEvent.stopPropagation();
    }
    
    // Find the event to get its title for confirmation
    const event = eventData?.find(e => e.id === eventId);
    const eventTitle = event ? event.title : `Event ${eventId}`;
    
    // Show confirmation dialog
    const confirmed = confirm(`Are you sure you want to delete "${eventTitle}"?\n\nThis action cannot be undone.`);
    if (!confirmed) return;
    
    try {
        // Show loading state on the button
        const deleteBtn = document.querySelector(`button[onclick*="deleteEvent(${eventId}"]`);
        if (deleteBtn) {
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            deleteBtn.disabled = true;
        }
        
        // Call delete API
        const response = await fetch(`/api/delete-event/${eventId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success notification
            showNotification(`Event "${eventTitle}" deleted successfully`, 'success');
            
            // Refresh the data to update all views
            await loadInitialData();
        } else {
            throw new Error(result.message || 'Failed to delete event');
        }
        
    } catch (error) {
        console.error('Error deleting event:', error);
        
        // Reset button state
        const deleteBtn = document.querySelector(`button[onclick*="deleteEvent(${eventId}"]`);
        if (deleteBtn) {
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
            deleteBtn.disabled = false;
        }
        
        // Show error notification
        if (error.message.includes('404') || (error.response && error.response.status === 404)) {
            showNotification(`Event not found - it may have already been deleted`, 'error');
            // Refresh data anyway to update the view
            await loadInitialData();
        } else {
            showNotification(`Failed to delete event: ${error.message}`, 'error');
        }
    }
}

// Switch map layers
function switchMapLayer(layer) {
    console.log('Switching to layer:', layer);
    // For MVP, we'll just update the current view
    updateMapMarkers();
}

// Reset map to initial view
function resetMapView() {
    if (map && map.initialCenter && map.initialZoom) {
        map.setView(map.initialCenter, map.initialZoom);
        
        // Optional: Close any open popups
        map.closePopup();
        
        console.log('Map reset to initial view');
    }
}

// Handle image upload and analysis
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const analysisType = document.getElementById('analysis-type').value;
    
    showLoading('Analyzing satellite image...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('analysis_type', analysisType);

        const response = await fetch('/api/analyze-image', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            
            // Switch to intelligence view and show result
            switchView('intelligence');
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('intelligence-tab').classList.add('active');
            
            showAnalysisResult('Image Analysis', result.analysis);
        } else {
            throw new Error('Analysis failed');
        }
    } catch (error) {
        console.error('Error analyzing image:', error);
        showNotification('Error analyzing image. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Handle audio upload and transcription
async function handleAudioUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    showLoading('Transcribing audio...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/transcribe-audio', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            
            // Switch to intelligence view and show result
            switchView('intelligence');
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('intelligence-tab').classList.add('active');
            
            showAnalysisResult('Audio Transcription', result.transcription, result.analysis);
        } else {
            throw new Error('Transcription failed');
        }
    } catch (error) {
        console.error('Error transcribing audio:', error);
        showNotification('Error transcribing audio. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Send chat message to AI with streaming response
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';

    // Create AI message placeholder for streaming
    const aiMessageDiv = createStreamingMessage();

    try {
        const formData = new FormData();
        formData.append('message', message);

        const response = await fetch('/api/chat-stream', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Streaming request failed');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let aiResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.error) {
                            updateStreamingMessage(aiMessageDiv, `Error: ${data.error}`);
                            return;
                        }
                        
                        if (data.done) {
                            // Stream complete
                            finalizeStreamingMessage(aiMessageDiv);
                            return;
                        }
                        
                        if (data.chunk) {
                            aiResponse += data.chunk;
                            updateStreamingMessage(aiMessageDiv, aiResponse);
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error sending streaming chat message:', error);
        updateStreamingMessage(aiMessageDiv, 'Sorry, I encountered an error. Please try again.');
    }
}

// Create a streaming message container
function createStreamingMessage() {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message streaming';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <strong>AI Agent:</strong>
            <div class="markdown-content streaming-content"></div>
            <span class="cursor">|</span>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// Configure markdown parser for security and styling
function configureMarkdown() {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            sanitize: false, // We'll handle this ourselves
            highlight: function(code, lang) {
                // Basic syntax highlighting could be added here
                return code;
            }
        });
    }
}

// Update streaming message content with real-time markdown rendering
function updateStreamingMessage(messageDiv, content) {
    const contentDiv = messageDiv.querySelector('.streaming-content');
    if (contentDiv && typeof marked !== 'undefined') {
        // Store the original content for final rendering
        contentDiv.dataset.originalContent = content;
        
        try {
            // Pre-process content to handle incomplete markdown gracefully
            let processedContent = content;
            
            // Handle incomplete code blocks
            const codeBlockMatches = content.match(/```[\s\S]*$/);
            if (codeBlockMatches && !content.endsWith('```')) {
                // Add temporary closing to incomplete code block
                processedContent = content + '\n```';
            }
            
            // Handle incomplete tables (basic check)
            const lines = content.split('\n');
            const lastLine = lines[lines.length - 1];
            if (lastLine && lastLine.includes('|') && !lastLine.trim().endsWith('|')) {
                // Don't render incomplete table rows
                processedContent = lines.slice(0, -1).join('\n');
            }
            
            // Parse the processed content as markdown
            const renderedContent = marked.parse(processedContent);
            contentDiv.innerHTML = renderedContent;
            
        } catch (e) {
            // If markdown parsing fails, show as plain text with basic formatting
            contentDiv.innerHTML = content.replace(/\n/g, '<br>');
        }
        
        // Auto-scroll to bottom
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Finalize streaming message
function finalizeStreamingMessage(messageDiv) {
    if (messageDiv) {
        // Remove streaming class to hide cursor
        messageDiv.classList.remove('streaming');
        
        // Remove the cursor element
        const cursor = messageDiv.querySelector('.cursor');
        if (cursor) {
            cursor.remove();
        }
        
        // Get the original content and ensure final render is clean
        const contentDiv = messageDiv.querySelector('.streaming-content');
        if (contentDiv && typeof marked !== 'undefined') {
            // Get the accumulated text content from the streaming process
            const accumulatedContent = contentDiv.dataset.originalContent || 
                                     contentDiv.textContent || 
                                     contentDiv.innerText || '';
            
            try {
                // Final clean render without streaming artifacts
                contentDiv.innerHTML = marked.parse(accumulatedContent);
            } catch (e) {
                // Fallback to basic HTML
                contentDiv.innerHTML = accumulatedContent.replace(/\n/g, '<br>');
            }
        }
    }
}

// Add message to chat with markdown support
function addChatMessage(message, sender, isTemporary = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    if (isTemporary) messageDiv.classList.add('temporary');
    
    const prefix = sender === 'user' ? '<strong>You:</strong> ' : '<strong>AI Agent:</strong> ';
    
    // Render markdown for AI messages, plain text for user messages
    let content;
    if (sender === 'ai' && typeof marked !== 'undefined') {
        content = `${prefix}<div class="markdown-content">${marked.parse(message)}</div>`;
    } else {
        content = `${prefix}${message}`;
    }
    
    messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// Update intelligence summary
function updateIntelligenceSummary(intelligence) {
    const summaryDiv = document.getElementById('intelligence-summary');
    if (summaryDiv) {
        summaryDiv.innerHTML = intelligence.summary || 'No intelligence summary available.';
    }
    
    // Update metrics if available
    if (intelligence.event_count !== undefined) {
        const eventCountElement = document.getElementById('event-count');
        if (eventCountElement) {
            eventCountElement.textContent = intelligence.event_count;
        }
    }
    if (intelligence.regions_monitored !== undefined) {
        const regionsElement = document.getElementById('regions-monitored');
        if (regionsElement) {
            regionsElement.textContent = intelligence.regions_monitored;
        }
    }
}

// Update header statistics
function updateHeaderStats() {
    document.getElementById('event-count').textContent = eventData.length;
    document.getElementById('regions-monitored').textContent = new Set(eventData.map(e => e.location)).size;
}

// Show analysis result
function showAnalysisResult(title, content, additional = null) {
    const analysisMessage = `
        <strong>${title}:</strong><br>
        ${content}
        ${additional ? `<br><br><strong>Additional Analysis:</strong><br>${JSON.stringify(additional, null, 2)}` : ''}
    `;
    addChatMessage(analysisMessage, 'ai');
}

// Show loading overlay
function showLoading(message = 'Processing intelligence data...') {
    const overlay = document.getElementById('loading-overlay');
    const messageElement = overlay.querySelector('p');
    messageElement.textContent = message;
    overlay.style.display = 'flex';
}

// Hide loading overlay
function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// Show notification
function showNotification(message, type = 'info') {
    console.log(`${type.toUpperCase()}: ${message}`);
    addChatMessage(`System: ${message}`, 'ai');
}

// Auto-refresh data every 30 seconds
function startAutoRefresh() {
    setInterval(async () => {
        try {
            const response = await fetch('/api/events');
            if (response.ok) {
                const eventsData = await response.json();
                const newEventCount = eventsData.events?.length || 0;
                
                if (newEventCount !== eventData.length) {
                    eventData = eventsData.events || [];
                    updateEventList();
                    updateMapMarkers();
                    updateHeaderStats();
                    updateMetrics();
                    updateCharts();
                    
                    showNotification(`Updated: ${newEventCount} events detected`, 'info');
                }
            }
        } catch (error) {
            console.error('Auto-refresh error:', error);
        }
    }, 30000); // 30 seconds
}

// Health check function
async function checkSystemHealth() {
    try {
        const response = await fetch('/api/health');
        if (response.ok) {
            const health = await response.json();
            const statusElement = document.getElementById('system-status');
            const dot = statusElement.querySelector('.status-dot');
            
            if (health.status === 'healthy') {
                dot.classList.add('active');
                statusElement.querySelector('span:last-child').textContent = 'System Online';
            } else {
                dot.classList.remove('active');
                statusElement.querySelector('span:last-child').textContent = 'System Issues';
            }
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// Check system health every minute
setInterval(checkSystemHealth, 60000);

// Map chat sidebar functionality
function toggleMapChatSidebar() {
    const mapChatSidebar = document.getElementById('map-chat-sidebar');
    const mapChatToggle = document.getElementById('map-chat-toggle');
    const mapContent = document.querySelector('.map-content');
    
    if (mapChatSidebar && mapContent && mapChatToggle) {
        if (mapChatSidebar.classList.contains('open')) {
            // Close sidebar
            mapChatSidebar.classList.remove('open');
            mapContent.classList.remove('chat-open');
            mapChatToggle.classList.remove('active');
        } else {
            // Open sidebar
            mapChatSidebar.classList.add('open');
            mapContent.classList.add('chat-open');
            mapChatToggle.classList.add('active');
        }
        
        // Smooth map resizing during transition
        if (map) {
            // Invalidate map size at multiple points during the transition for smoother animation
            const transitionDuration = 300;
            const steps = 5;
            const stepDelay = transitionDuration / steps;
            
            for (let i = 1; i <= steps; i++) {
                setTimeout(() => {
                    if (map) {
                        map.invalidateSize();
                    }
                }, stepDelay * i);
            }
        }
    }
}

function closeMapChatSidebar() {
    const mapChatSidebar = document.getElementById('map-chat-sidebar');
    const mapChatToggle = document.getElementById('map-chat-toggle');
    const mapContent = document.querySelector('.map-content');
    
    if (mapChatSidebar && mapContent && mapChatToggle) {
        mapChatSidebar.classList.remove('open');
        mapContent.classList.remove('chat-open');
        mapChatToggle.classList.remove('active');
        
        // Smooth map resizing during transition
        if (map) {
            // Invalidate map size at multiple points during the transition for smoother animation
            const transitionDuration = 300;
            const steps = 5;
            const stepDelay = transitionDuration / steps;
            
            for (let i = 1; i <= steps; i++) {
                setTimeout(() => {
                    if (map) {
                        map.invalidateSize();
                    }
                }, stepDelay * i);
            }
        }
    }
}

async function sendMapChatMessage() {
    const mapChatInput = document.getElementById('map-chat-input');
    const message = mapChatInput.value.trim();
    
    if (!message) return;

    // Add user message to map chat
    addMapChatMessage(message, 'user');
    mapChatInput.value = '';

    // Create AI message placeholder for streaming
    const aiMessageDiv = createMapStreamingMessage();

    try {
        const formData = new FormData();
        formData.append('message', message);

        const response = await fetch('/api/chat-stream', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Streaming request failed');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let aiResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.error) {
                            updateMapStreamingMessage(aiMessageDiv, `Error: ${data.error}`);
                            return;
                        }
                        
                        if (data.done) {
                            // Stream complete
                            finalizeMapStreamingMessage(aiMessageDiv);
                            return;
                        }
                        
                        if (data.chunk) {
                            aiResponse += data.chunk;
                            updateMapStreamingMessage(aiMessageDiv, aiResponse);
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error sending streaming chat message:', error);
        updateMapStreamingMessage(aiMessageDiv, 'Sorry, I encountered an error. Please try again.');
    }
}

// Map chat message functions
function addMapChatMessage(message, sender, isTemporary = false) {
    const chatMessages = document.getElementById('map-chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    if (isTemporary) messageDiv.classList.add('temporary');
    
    const prefix = sender === 'user' ? '<strong>You:</strong> ' : '<strong>AI Agent:</strong> ';
    
    // Render markdown for AI messages, plain text for user messages
    let content;
    if (sender === 'ai' && typeof marked !== 'undefined') {
        content = `${prefix}<div class="markdown-content">${marked.parse(message)}</div>`;
    } else {
        content = `${prefix}${message}`;
    }
    
    messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function createMapStreamingMessage() {
    const chatMessages = document.getElementById('map-chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message streaming';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <strong>AI Agent:</strong>
            <div class="markdown-content streaming-content"></div>
            <span class="cursor">|</span>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function updateMapStreamingMessage(messageDiv, content) {
    const contentDiv = messageDiv.querySelector('.streaming-content');
    if (contentDiv && typeof marked !== 'undefined') {
        // Store the original content for final rendering
        contentDiv.dataset.originalContent = content;
        
        try {
            // Pre-process content to handle incomplete markdown gracefully
            let processedContent = content;
            
            // Handle incomplete code blocks
            const codeBlockMatches = content.match(/```[\s\S]*$/);
            if (codeBlockMatches && !content.endsWith('```')) {
                // Add temporary closing to incomplete code block
                processedContent = content + '\n```';
            }
            
            // Handle incomplete tables (basic check)
            const lines = content.split('\n');
            const lastLine = lines[lines.length - 1];
            if (lastLine && lastLine.includes('|') && !lastLine.trim().endsWith('|')) {
                // Don't render incomplete table rows
                processedContent = lines.slice(0, -1).join('\n');
            }
            
            // Parse the processed content as markdown
            const renderedContent = marked.parse(processedContent);
            contentDiv.innerHTML = renderedContent;
            
        } catch (e) {
            // If markdown parsing fails, show as plain text with basic formatting
            contentDiv.innerHTML = content.replace(/\n/g, '<br>');
        }
        
        // Auto-scroll to bottom
        const chatMessages = document.getElementById('map-chat-messages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function finalizeMapStreamingMessage(messageDiv) {
    if (messageDiv) {
        // Remove streaming class to hide cursor
        messageDiv.classList.remove('streaming');
        
        // Remove the cursor element
        const cursor = messageDiv.querySelector('.cursor');
        if (cursor) {
            cursor.remove();
        }
        
        // Get the original content and ensure final render is clean
        const contentDiv = messageDiv.querySelector('.streaming-content');
        if (contentDiv && typeof marked !== 'undefined') {
            // Get the accumulated text content from the streaming process
            const accumulatedContent = contentDiv.dataset.originalContent || 
                                     contentDiv.textContent || 
                                     contentDiv.innerText || '';
            
            try {
                // Final clean render without streaming artifacts
                contentDiv.innerHTML = marked.parse(accumulatedContent);
            } catch (e) {
                // Fallback to basic HTML
                contentDiv.innerHTML = accumulatedContent.replace(/\n/g, '<br>');
            }
        }
    }
}

// Web Search Functions
async function handleWebSearchPreview() {
    const query = document.getElementById('web-search-query').value.trim();
    const statusDiv = document.getElementById('web-search-status');
    
    if (!query) {
        statusDiv.textContent = 'Please enter a search query';
        statusDiv.style.color = '#ef4444';
        return;
    }
    
    // Create streaming preview modal
    const previewModal = createWebSearchStreamModal(query);
    document.body.appendChild(previewModal);
    
    // Reset status
    statusDiv.textContent = '';
    
    try {
        const formData = new FormData();
        formData.append('query', query);
        formData.append('max_events', '5');
        
        const response = await fetch('/api/web-search-stream', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Streaming request failed');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        const foundEvents = [];

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'status') {
                            updateWebSearchStreamStatus(previewModal, data.message);
                        } else if (data.type === 'event') {
                            foundEvents.push(data.event);
                            addWebSearchStreamEvent(previewModal, data.event, foundEvents.length);
                        } else if (data.type === 'complete') {
                            completeWebSearchStream(previewModal, foundEvents);
                        } else if (data.type === 'error') {
                            showWebSearchStreamError(previewModal, data.message);
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Web search streaming error:', error);
        showWebSearchStreamError(previewModal, 'Search failed. Please try again.');
    }
}

function createWebSearchStreamModal(query) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay active';
    modal.innerHTML = `
        <div class="modal-content large-modal">
            <div class="modal-header">
                <h3><i class="fas fa-search"></i> Web Search: "${query}"</h3>
                <button class="close-btn" onclick="closeWebSearchStreamModal(this)">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="search-stream-status">
                    <div class="status-indicator">
                        <div class="loading-spinner"></div>
                        <span class="status-text">Initializing search...</span>
                    </div>
                </div>
                <div class="search-stream-events">
                    <h4>Found Events:</h4>
                    <div class="events-container"></div>
                </div>
                <div class="search-stream-actions" style="display: none;">
                    <button class="btn btn--primary" onclick="addAllWebSearchStreamEvents(this)">
                        <i class="fas fa-plus"></i> Add All Events to Map
                    </button>
                    <button class="btn btn--secondary" onclick="closeWebSearchStreamModal(this)">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;
    return modal;
}

function updateWebSearchStreamStatus(modal, message) {
    const statusText = modal.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = message;
    }
}

function addWebSearchStreamEvent(modal, event, eventNumber) {
    const eventsContainer = modal.querySelector('.events-container');
    const eventDiv = document.createElement('div');
    eventDiv.className = 'stream-event-item';
    eventDiv.style.animation = 'slideInRight 0.3s ease-out';
    
    eventDiv.innerHTML = `
        <div class="event-header">
            <span class="event-number">#${eventNumber}</span>
            <h5>${event.title}</h5>
            <div class="event-badges">
                <span class="badge badge--${event.severity}">${event.severity.toUpperCase()}</span>
                <span class="badge badge--category">${formatEventTypeName(event.category)}</span>
            </div>
        </div>
        <p class="event-description">${event.description}</p>
        <div class="event-meta">
            <span><i class="fas fa-map-marker-alt"></i> ${event.location}</span>
            <span><i class="fas fa-clock"></i> ${new Date(event.timestamp).toLocaleDateString()}</span>
        </div>
    `;
    
    if (eventsContainer) {
        eventsContainer.appendChild(eventDiv);
        eventsContainer.scrollTop = eventsContainer.scrollHeight;
    }
}

function completeWebSearchStream(modal, events) {
    // Hide loading spinner
    const statusIndicator = modal.querySelector('.status-indicator');
    if (statusIndicator) {
        statusIndicator.innerHTML = `
            <i class="fas fa-check-circle" style="color: #10b981;"></i>
            <span class="status-text">Search completed! Found ${events.length} events.</span>
        `;
    }
    
    // Show actions
    const actions = modal.querySelector('.search-stream-actions');
    if (actions) {
        actions.style.display = 'flex';
        actions.dataset.events = JSON.stringify(events);
    }
}

function showWebSearchStreamError(modal, message) {
    const statusIndicator = modal.querySelector('.status-indicator');
    if (statusIndicator) {
        statusIndicator.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="color: #ef4444;"></i>
            <span class="status-text">${message}</span>
        `;
    }
}

function closeWebSearchStreamModal(element) {
    const modal = element.closest('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

async function addAllWebSearchStreamEvents(element) {
    const modal = element.closest('.modal-overlay');
    const eventsData = modal.querySelector('.search-stream-actions').dataset.events;
    
    if (!eventsData) return;
    
    try {
        const events = JSON.parse(eventsData);
        
        // Update button state
        element.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Adding Events...`;
        element.disabled = true;
        
        // Add events via integration endpoint
        const response = await fetch('/api/integrate-search-events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(events)
        });
        
        const result = await response.json();
        
        if (result.integration_result && result.integration_result.added_count > 0) {
            // Success
            element.innerHTML = `<i class="fas fa-check"></i> Added ${result.integration_result.added_count} Events!`;
            element.style.backgroundColor = '#10b981';
            
            // Refresh the map data
            await loadInitialData();
            
            // Show notification
            showNotification(`Added ${result.integration_result.added_count} new security events`, 'success');
            
            // Close modal after short delay
            setTimeout(() => closeWebSearchStreamModal(element), 2000);
        } else {
            throw new Error('Failed to integrate events');
        }
        
    } catch (error) {
        console.error('Error adding events:', error);
        element.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error Adding Events`;
        element.style.backgroundColor = '#ef4444';
        element.disabled = false;
    }
}

async function toggleSearchAgents() {
    const button = document.getElementById('deploy-search-agents-btn');
    const query = document.getElementById('web-search-query').value.trim();
    const statusDiv = document.getElementById('web-search-status');
    const isDeployed = button.dataset.deployed === 'true';
    
    if (isDeployed) {
        // Stop all agents
        await stopAllSearchAgents();
    } else {
        // Deploy agents
        if (!query) {
            statusDiv.textContent = 'Please enter search terms (comma-separated)';
            statusDiv.style.color = '#ef4444';
            return;
        }
        
        const searchTerms = query.split(',').map(term => term.trim()).filter(term => term.length > 0);
        if (searchTerms.length === 0) {
            statusDiv.textContent = 'Please enter valid search terms';
            statusDiv.style.color = '#ef4444';
            return;
        }
        
        await deploySearchAgents(searchTerms);
    }
}

async function deploySearchAgents(searchTerms) {
    const button = document.getElementById('deploy-search-agents-btn');
    const statusDiv = document.getElementById('web-search-status');
    
    try {
        statusDiv.textContent = `Deploying ${searchTerms.length} search agents...`;
        statusDiv.style.color = '#3b82f6';
        
        // Update button state
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deploying...';
        button.disabled = true;
        
        // Deploy agents via API
        const response = await fetch('/api/deploy-search-agents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ search_terms: searchTerms })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Mark agents as active
            searchTerms.forEach(term => {
                activeAgents.set(term, {
                    term: term,
                    status: 'active',
                    eventsFound: 0,
                    deployedAt: new Date()
                });
            });
            
            // Update UI
            button.innerHTML = '<i class="fas fa-stop"></i> Stop Agents';
            button.classList.remove('btn--primary');
            button.classList.add('btn--secondary');
            button.dataset.deployed = 'true';
            button.disabled = false;
            
            statusDiv.textContent = `${searchTerms.length} search agents deployed and monitoring`;
            statusDiv.style.color = '#10b981';
            
            // Update agent display
            updateActiveAgentsDisplay();
            
            // Start monitoring for events
            startAgentMonitoring();
            
            showNotification(`Deployed ${searchTerms.length} search agents`, 'success');
            
        } else {
            throw new Error(result.error || 'Failed to deploy agents');
        }
        
    } catch (error) {
        console.error('Error deploying agents:', error);
        button.innerHTML = '<i class="fas fa-robot"></i> Deploy Agents';
        button.disabled = false;
        statusDiv.textContent = `Deployment failed: ${error.message}`;
        statusDiv.style.color = '#ef4444';
    }
}

async function stopAllSearchAgents() {
    const button = document.getElementById('deploy-search-agents-btn');
    const statusDiv = document.getElementById('web-search-status');
    
    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
        button.disabled = true;
        
        // Stop agents via API
        const response = await fetch('/api/stop-search-agents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Clear active agents
            activeAgents.clear();
            
            // Update UI
            button.innerHTML = '<i class="fas fa-robot"></i> Deploy Agents';
            button.classList.remove('btn--secondary');
            button.classList.add('btn--primary');
            button.dataset.deployed = 'false';
            button.disabled = false;
            
            statusDiv.textContent = 'All search agents stopped';
            statusDiv.style.color = '#94a3b8';
            
            // Update agent display
            updateActiveAgentsDisplay();
            
            // Stop monitoring
            stopAgentMonitoring();
            
            showNotification('All search agents stopped', 'info');
            
        } else {
            throw new Error(result.error || 'Failed to stop agents');
        }
        
    } catch (error) {
        console.error('Error stopping agents:', error);
        button.innerHTML = '<i class="fas fa-stop"></i> Stop Agents';
        button.disabled = false;
        statusDiv.textContent = `Stop failed: ${error.message}`;
        statusDiv.style.color = '#ef4444';
    }
}

function updateActiveAgentsDisplay() {
    const container = document.getElementById('active-agents');
    if (!container) return;
    
    if (activeAgents.size === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = `
        <h4 style="color: #60a5fa; font-size: 0.9rem; margin-bottom: 0.5rem;">Active Agents:</h4>
        ${Array.from(activeAgents.values()).map(agent => `
            <div class="agent-item">
                <div class="agent-term">${agent.term}</div>
                <div class="agent-status">
                    <div class="agent-status-dot"></div>
                    <span class="agent-status-text">Active</span>
                    <span class="agent-events-count">${agent.eventsFound} events</span>
                    <button class="stop-agent-btn" onclick="stopSingleAgent('${agent.term}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('')}
    `;
}

async function stopSingleAgent(searchTerm) {
    try {
        const response = await fetch('/api/stop-single-agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ search_term: searchTerm })
        });
        
        const result = await response.json();
        
        if (result.success) {
            activeAgents.delete(searchTerm);
            updateActiveAgentsDisplay();
            
            // If no agents left, update main button
            if (activeAgents.size === 0) {
                const button = document.getElementById('deploy-search-agents-btn');
                const statusDiv = document.getElementById('web-search-status');
                
                button.innerHTML = '<i class="fas fa-robot"></i> Deploy Agents';
                button.classList.remove('btn--secondary');
                button.classList.add('btn--primary');
                button.dataset.deployed = 'false';
                
                statusDiv.textContent = 'All search agents stopped';
                statusDiv.style.color = '#94a3b8';
                
                stopAgentMonitoring();
            }
            
            showNotification(`Stopped agent: ${searchTerm}`, 'info');
        }
    } catch (error) {
        console.error('Error stopping single agent:', error);
        showNotification(`Failed to stop agent: ${searchTerm}`, 'error');
    }
}

let agentMonitoringInterval;

function startAgentMonitoring() {
    // Poll for new events every 30 seconds
    agentMonitoringInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/agent-status');
            const result = await response.json();
            
            if (result.success && result.agents) {
                // Update agent status
                result.agents.forEach(agentStatus => {
                    if (activeAgents.has(agentStatus.term)) {
                        const agent = activeAgents.get(agentStatus.term);
                        agent.eventsFound = agentStatus.events_found;
                        agent.status = agentStatus.status;
                    }
                });
                
                updateActiveAgentsDisplay();
                
                // Refresh map if new events were found
                if (result.new_events_count > 0) {
                    await loadInitialData();
                    showNotification(`${result.new_events_count} new events found by search agents`, 'success');
                }
            }
        } catch (error) {
            console.error('Error monitoring agents:', error);
        }
    }, 30000); // 30 seconds
}

function stopAgentMonitoring() {
    if (agentMonitoringInterval) {
        clearInterval(agentMonitoringInterval);
        agentMonitoringInterval = null;
    }
}

function showWebSearchResults(events) {
    let content = '<h3>Found Events Preview:</h3><ul>';
    events.forEach(event => {
        content += `
            <li style="margin-bottom: 1rem; padding: 0.5rem; border: 1px solid #404040; border-radius: 4px;">
                <strong>${event.title}</strong><br>
                <small style="color: #94a3b8;">Location: ${event.location} | Severity: ${event.severity} | Category: ${event.category}</small><br>
                <p style="margin: 0.5rem 0; font-size: 0.9rem;">${event.description}</p>
            </li>
        `;
    });
    content += '</ul>';
    
    showAnalysisResult('Web Search Preview', content);
}

// Global agent management
let activeAgents = new Map(); // Map of search term -> agent status

// Add event listeners for web search agents
document.addEventListener('DOMContentLoaded', function() {
    // Existing event listeners...
    
    // Web search functionality
    const webSearchPreviewBtn = document.getElementById('web-search-preview-btn');
    const deployAgentsBtn = document.getElementById('deploy-search-agents-btn');
    const webSearchQuery = document.getElementById('web-search-query');
    
    if (webSearchPreviewBtn) {
        webSearchPreviewBtn.addEventListener('click', handleWebSearchPreview);
    }
    
    if (deployAgentsBtn) {
        deployAgentsBtn.addEventListener('click', toggleSearchAgents);
    }
    
    if (webSearchQuery) {
        webSearchQuery.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                toggleSearchAgents();
            }
        });
    }
}); 