const { createApp } = Vue;

const API_URL = 'http://127.0.0.1:8000';

// Main Content Component (80%)
const MainContent = {
    template: `
        <div class="main-content">
            <!-- Graph Section (Full height) -->
            <div class="graph-section">
                <h1>{{ title }}</h1>
                <p class="stats">Total crashes in dataset: <strong>{{ totalCrashes.toLocaleString() }}</strong></p>
                <div class="graph-container">
                    <iframe 
                        :key="mapKey"
                        :src="mapUrl" 
                        class="map-iframe"
                        frameborder="0"
                    ></iframe>
                </div>
            </div>
            
            <!-- Sliding Ranking Panel -->
            <div class="ranking-panel" :class="{ 'panel-open': panelOpen }">
                <button class="panel-toggle" @click="togglePanel">
                    <span class="toggle-icon">{{ panelOpen ? '▼' : '▲' }}</span>
                    <span>{{ panelOpen ? 'Hide Rankings' : 'Show Rankings' }}</span>
                </button>
                
                <div class="ranking-content">
                    <h2>Crash Rankings</h2>
                    <div v-if="loading" class="loading">Loading data...</div>
                    <div v-else-if="error" class="error">{{ error }}</div>
                    <div v-else class="table-wrapper">
                        <table class="ranking-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>{{ groupBy === 'street' ? 'Street Name' : 'Location' }}</th>
                                    <th>Crashes</th>
                                    <th>Per Month</th>
                                    <th v-if="rankType !== 'frequency'">Fatal</th>
                                    <th v-if="rankType !== 'frequency'">Incapacitating</th>
                                    <th v-if="rankType !== 'frequency'">Non-Incap.</th>
                                    <th v-if="rankType !== 'frequency'">Injury Score</th>
                                    <th v-if="rankType === 'dangerous'">Avg Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(item, index) in ranking" :key="index">
                                    <td>{{ index + 1 }}</td>
                                    <td>{{ item.name }}</td>
                                    <td>{{ item.COUNT }}</td>
                                    <td>{{ item.CRASHES_PER_MONTH?.toFixed(2) || 0 }}</td>
                                    <td v-if="rankType !== 'frequency'">{{ item.INJURIES_FATAL || 0 }}</td>
                                    <td v-if="rankType !== 'frequency'">{{ item.INJURIES_INCAPACITATING || 0 }}</td>
                                    <td v-if="rankType !== 'frequency'">{{ item.INJURIES_NON_INCAPACITATING || 0 }}</td>
                                    <td v-if="rankType !== 'frequency'">{{ item.INJURY_SCORE?.toFixed(1) || 0 }}</td>
                                    <td v-if="rankType === 'dangerous'">{{ item.AVERAGE_INJURY_SCORE?.toFixed(3) || 0 }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `,
    props: ['rankType', 'groupBy', 'filters'],
    data() {
        return {
            title: 'High Risk Intersections',
            ranking: [],
            totalCrashes: 0,
            loading: true,
            error: null,
            panelOpen: false
        };
    },
    computed: {
        mapKey() {
            // Generate a unique key based on all filter values to force iframe refresh
            if (!this.filters) return 'default';
            return JSON.stringify(this.filters);
        },
        mapUrl() {
            const params = new URLSearchParams();
            if (this.filters) {
                if (this.filters.dateStart) params.append('date_start', this.filters.dateStart);
                if (this.filters.dateEnd) params.append('date_end', this.filters.dateEnd);
                if (this.filters.damage.length) params.append('damage', this.filters.damage.join(','));
                if (this.filters.crashType.length) params.append('crash_type', this.filters.crashType.join(','));
                if (this.filters.injuries.length) params.append('injuries', this.filters.injuries.join(','));
                if (this.filters.cause.length) params.append('cause', this.filters.cause.join(','));
                if (this.filters.lighting.length) params.append('lighting', this.filters.lighting.join(','));
            }
            return `${API_URL}/api/map?${params}`;
        }
    },
    watch: {
        rankType() { this.fetchRanking(); },
        groupBy() { this.fetchRanking(); },
        filters: {
            handler() { this.fetchRanking(); },
            deep: true
        }
    },
    mounted() {
        this.fetchRanking();
    },
    methods: {
        togglePanel() {
            this.panelOpen = !this.panelOpen;
        },
        async fetchRanking() {
            this.loading = true;
            this.error = null;
            try {
                const params = new URLSearchParams({
                    rank_type: this.rankType,
                    group_by: this.groupBy,
                    limit: 10
                });
                
                // Add filter parameters
                if (this.filters) {
                    if (this.filters.dateStart) params.append('date_start', this.filters.dateStart);
                    if (this.filters.dateEnd) params.append('date_end', this.filters.dateEnd);
                    if (this.filters.damage.length) params.append('damage', this.filters.damage.join(','));
                    if (this.filters.crashType.length) params.append('crash_type', this.filters.crashType.join(','));
                    if (this.filters.injuries.length) params.append('injuries', this.filters.injuries.join(','));
                    if (this.filters.cause.length) params.append('cause', this.filters.cause.join(','));
                    if (this.filters.lighting.length) params.append('lighting', this.filters.lighting.join(','));
                }
                
                const response = await fetch(`${API_URL}/api/ranking?${params}`);
                const data = await response.json();
                
                if (data.error) {
                    this.error = data.error;
                } else {
                    this.ranking = data.ranking;
                    this.totalCrashes = data.total_crashes;
                }
            } catch (err) {
                this.error = 'Failed to connect to API. Make sure the server is running (python api.py)';
            }
            this.loading = false;
        }
    }
};

// Sidebar Component (20%)
const SideBar = {
    template: `
        <div class="sidebar">
            <h2>Settings</h2>
            
            <!-- Rank By -->
            <div class="filter-group">
                <label>
                    Rank By:
                    <span class="tooltip-wrapper">
                        <span class="tooltip-icon">?</span>
                        <span class="tooltip-content">
                            <strong>Frequent:</strong> Total crash count<br>
                            <strong>Weighted:</strong> By injury severity score<br>
                            <strong>Dangerous:</strong> Average injury per crash
                        </span>
                    </span>
                </label>
                <select v-model="selectedRankType" @change="emitChanges">
                    <option value="frequency">Most Frequent</option>
                    <option value="weighted">Weighted by Injury</option>
                    <option value="dangerous">Most Dangerous</option>
                </select>
            </div>
            
            <!-- Group By -->
            <div class="filter-group">
                <label>
                    Group By:
                    <span class="tooltip-wrapper">
                        <span class="tooltip-icon">?</span>
                        <span class="tooltip-content">
                            <strong>Street:</strong> Group crashes by street name<br>
                            <strong>Location:</strong> Group by coordinate bins (lat/long)
                        </span>
                    </span>
                </label>
                <select v-model="selectedGroupBy" @change="emitChanges">
                    <option value="street">Street</option>
                    <option value="location">Location</option>
                </select>
            </div>
            
            <h3 class="filter-header">Filters</h3>
            
            <!-- Date Range -->
            <div class="filter-group">
                <label>Date Range:</label>
                <input type="date" v-model="filters.dateStart" @change="emitChanges">
                <input type="date" v-model="filters.dateEnd" @change="emitChanges">
            </div>
            
            <!-- Damage -->
            <div class="filter-group">
                <label>Damage:</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" value="$500 OR LESS" v-model="filters.damage" @change="emitChanges">
                        $500 or Less
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="$501 - $1,500" v-model="filters.damage" @change="emitChanges">
                        $501 - $1,500
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="OVER $1,500" v-model="filters.damage" @change="emitChanges">
                        Over $1,500
                    </label>
                </div>
            </div>
            
            <!-- Crash Type -->
            <div class="filter-group">
                <label>Crash Type:</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" value="NO INJURY / DRIVE AWAY" v-model="filters.crashType" @change="emitChanges">
                        No Injury / Drive Away
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="INJURY AND / OR TOW DUE TO CRASH" v-model="filters.crashType" @change="emitChanges">
                        Injury / Tow
                    </label>
                </div>
            </div>
            
            <!-- Injuries -->
            <div class="filter-group">
                <label>Injuries:</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" value="none" v-model="filters.injuries" @change="emitChanges">
                        No Injury
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="non_incapacitating" v-model="filters.injuries" @change="emitChanges">
                        Non-Incapacitating
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="incapacitating" v-model="filters.injuries" @change="emitChanges">
                        Incapacitating
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="fatal" v-model="filters.injuries" @change="emitChanges">
                        Fatal
                    </label>
                </div>
            </div>
            
            <!-- Cause -->
            <div class="filter-group">
                <label>Cause:</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" value="user" v-model="filters.cause" @change="emitChanges">
                        User Error
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="non_user" v-model="filters.cause" @change="emitChanges">
                        Non-User Error
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="vehicle" v-model="filters.cause" @change="emitChanges">
                        Vehicle Error
                    </label>
                </div>
            </div>
            
            <!-- Lighting -->
            <div class="filter-group">
                <label>Lighting:</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" value="DAYLIGHT" v-model="filters.lighting" @change="emitChanges">
                        Daylight
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="DARKNESS, LIGHTED ROAD" v-model="filters.lighting" @change="emitChanges">
                        Dark (Lighted)
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="DARKNESS" v-model="filters.lighting" @change="emitChanges">
                        Dark (Unlighted)
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="DAWN" v-model="filters.lighting" @change="emitChanges">
                        Dawn
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" value="DUSK" v-model="filters.lighting" @change="emitChanges">
                        Dusk
                    </label>
                </div>
            </div>
            
            <button class="reset-btn" @click="resetFilters">Reset Filters</button>
        </div>
    `,
    data() {
        return {
            selectedRankType: 'frequency',
            selectedGroupBy: 'street',
            filters: {
                dateStart: '2017-10-24',
                dateEnd: '2025-10-24',
                damage: [],
                crashType: [],
                injuries: [],
                cause: [],
                lighting: []
            }
        };
    },
    methods: {
        emitChanges() {
            this.$emit('settings-changed', {
                rankType: this.selectedRankType,
                groupBy: this.selectedGroupBy,
                filters: { ...this.filters }
            });
        },
        resetFilters() {
            this.filters = {
                dateStart: '2017-10-24',
                dateEnd: '2025-10-24',
                damage: [],
                crashType: [],
                injuries: [],
                cause: [],
                lighting: []
            };
            this.emitChanges();
        }
    }
};

// Create and mount the Vue app
const app = createApp({
    data() {
        return {
            rankType: 'frequency',
            groupBy: 'street',
            filters: {
                dateStart: '2017-10-24',
                dateEnd: '2025-10-24',
                damage: [],
                crashType: [],
                injuries: [],
                cause: [],
                lighting: []
            }
        };
    },
    methods: {
        updateSettings(settings) {
            this.rankType = settings.rankType;
            this.groupBy = settings.groupBy;
            this.filters = settings.filters;
        }
    },
    template: `
        <div class="container">
            <main-content :rank-type="rankType" :group-by="groupBy" :filters="filters"></main-content>
            <side-bar @settings-changed="updateSettings"></side-bar>
        </div>
    `
});

app.component('main-content', MainContent);
app.component('side-bar', SideBar);

app.mount('#app');
