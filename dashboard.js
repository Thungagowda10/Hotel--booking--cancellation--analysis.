// Dashboard Interactive Application Logic
document.addEventListener('DOMContentLoaded', () => {
  const data = window.DASHBOARD_DATA;
  if (!data) {
    console.error('DASHBOARD_DATA not loaded');
    return;
  }

  // Global state for filtering
  let currentHotelFilter = 'ALL';
  let chartInstances = {};

  // Initialize Elements
  initTabs();
  initHotelFilter();
  renderKPIs(currentHotelFilter);
  renderAllCharts(currentHotelFilter);
  initRiskSimulator();
  renderFeatureImportance();
  renderBookingsTable();

  // Tab switching logic
  function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        
        tab.classList.add('active');
        const targetId = tab.getAttribute('data-tab');
        const targetPane = document.getElementById(targetId);
        if (targetPane) {
          targetPane.classList.add('active');
          // Resize charts when tab becomes visible
          window.dispatchEvent(new Event('resize'));
        }
      });
    });
  }

  // Hotel selector filter
  function initHotelFilter() {
    const selector = document.getElementById('hotelFilterSelect');
    if (selector) {
      selector.addEventListener('change', (e) => {
        currentHotelFilter = e.target.value;
        renderKPIs(currentHotelFilter);
        renderAllCharts(currentHotelFilter);
      });
    }
  }

  // Render / Update Top Metric Cards
  function renderKPIs(filter) {
    const kpi = data.kpis;
    let total = kpi.total_bookings;
    let canceled = kpi.total_cancellations;
    let rate = kpi.cancellation_rate;
    let adr = kpi.avg_adr;
    let leadTime = kpi.avg_lead_time;
    let subtext = `City: ${kpi.city_cancel_rate}% | Resort: ${kpi.resort_cancel_rate}%`;

    if (filter === 'City Hotel') {
      const city = data.by_hotel.find(h => h.hotel === 'City Hotel');
      total = city.total;
      canceled = city.canceled;
      rate = city.cancel_rate;
      adr = city.avg_adr;
      leadTime = city.avg_lead_time;
      subtext = 'Primary driver: High OTA & group block volume';
    } else if (filter === 'Resort Hotel') {
      const resort = data.by_hotel.find(h => h.hotel === 'Resort Hotel');
      total = resort.total;
      canceled = resort.canceled;
      rate = resort.cancel_rate;
      adr = resort.avg_adr;
      leadTime = resort.avg_lead_time;
      subtext = 'Primary driver: Seasonal leisure stays & direct guests';
    }

    document.getElementById('kpiTotalBookings').textContent = total.toLocaleString();
    document.getElementById('kpiCancellations').textContent = canceled.toLocaleString();
    document.getElementById('kpiCancelRate').textContent = `${rate}%`;
    document.getElementById('kpiCancelSubtext').innerHTML = `<span class="highlight">${subtext}</span>`;
    document.getElementById('kpiAvgADR').textContent = `€${adr.toFixed(2)}`;
    document.getElementById('kpiLeadTime').textContent = `${leadTime.toFixed(0)} Days`;
  }

  // Helper to destroy and recreate Chart.js instances
  function getOrCreateChart(canvasId, config) {
    if (chartInstances[canvasId]) {
      chartInstances[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId).getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, config);
    return chartInstances[canvasId];
  }

  // Render Charts based on filter
  function renderAllCharts(filter) {
    renderLeadTimeChart();
    renderSeasonalityChart(filter);
    renderChannelChart();
    renderDepositChart();
    renderDriversRadarChart();
    renderCountryChart();
  }

  // Chart 1: Lead Time Decay Curve (Why guests cancel early vs late)
  function renderLeadTimeChart() {
    const buckets = data.lead_buckets;
    const labels = buckets.map(b => b.bucket);
    const cancelRates = buckets.map(b => b.cancel_rate);
    const totalVolumes = buckets.map(b => b.total);

    getOrCreateChart('leadTimeChart', {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'line',
            label: 'Cancellation Rate (%)',
            data: cancelRates,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
            borderWidth: 3,
            pointBackgroundColor: '#ef4444',
            pointRadius: 5,
            yAxisID: 'yRate',
            tension: 0.3
          },
          {
            type: 'bar',
            label: 'Total Bookings Volume',
            data: totalVolumes,
            backgroundColor: 'rgba(99, 102, 241, 0.4)',
            borderColor: '#6366f1',
            borderWidth: 1,
            borderRadius: 6,
            yAxisID: 'yVol'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } } },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#fff',
            bodyColor: '#cbd5e1',
            borderColor: '#334155',
            borderWidth: 1
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          yVol: {
            type: 'linear',
            position: 'left',
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#94a3b8' },
            title: { display: true, text: 'Booking Count', color: '#6366f1' }
          },
          yRate: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { color: '#ef4444', callback: v => v + '%' },
            title: { display: true, text: 'Cancel Rate (%)', color: '#ef4444' }
          }
        }
      }
    });
  }

  // Chart 2: Monthly Seasonality & Rate Trajectory
  function renderSeasonalityChart(filter) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    
    // Group monthly stats
    const cityData = months.map(m => {
      const found = data.by_month.find(x => x.month === m && x.hotel === 'City Hotel');
      return found ? found.cancel_rate : 0;
    });

    const resortData = months.map(m => {
      const found = data.by_month.find(x => x.month === m && x.hotel === 'Resort Hotel');
      return found ? found.cancel_rate : 0;
    });

    let datasets = [];
    if (filter === 'ALL') {
      datasets = [
        {
          label: 'City Hotel Cancel Rate (%)',
          data: cityData,
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5
        },
        {
          label: 'Resort Hotel Cancel Rate (%)',
          data: resortData,
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5
        }
      ];
    } else if (filter === 'City Hotel') {
      datasets = [{
        label: 'City Hotel Cancel Rate (%)',
        data: cityData,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.2)',
        fill: true,
        tension: 0.35,
        borderWidth: 3
      }];
    } else {
      datasets = [{
        label: 'Resort Hotel Cancel Rate (%)',
        data: resortData,
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.2)',
        fill: true,
        tension: 0.35,
        borderWidth: 3
      }];
    }

    getOrCreateChart('seasonalityChart', {
      type: 'line',
      data: { labels: months.map(m => m.slice(0, 3)), datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8' } },
          tooltip: {
            backgroundColor: '#1e293b',
            callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw}%` }
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#94a3b8', callback: v => v + '%' },
            suggestedMin: 15,
            suggestedMax: 50
          }
        }
      }
    });
  }

  // Chart 3: Distribution Channel Risk
  function renderChannelChart() {
    const channels = data.by_channel.filter(c => c.channel !== 'Undefined');
    const labels = channels.map(c => c.channel);
    const cancelRates = channels.map(c => c.cancel_rate);
    const totals = channels.map(c => c.total);

    getOrCreateChart('channelRiskChart', {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Cancellation Rate (%)',
          data: cancelRates,
          backgroundColor: cancelRates.map(r => r > 35 ? 'rgba(239, 68, 68, 0.65)' : 'rgba(16, 185, 129, 0.65)'),
          borderColor: cancelRates.map(r => r > 35 ? '#ef4444' : '#10b981'),
          borderWidth: 1.5,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => `Total Bookings: ${totals[ctx.dataIndex].toLocaleString()}`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#94a3b8', callback: v => v + '%' },
            max: 50
          }
        }
      }
    });
  }

  // Chart 4: Non-Refundable Deposit Paradox
  function renderDepositChart() {
    const deposits = data.by_deposit;
    const labels = deposits.map(d => d.deposit_type);
    const rates = deposits.map(d => d.cancel_rate);

    getOrCreateChart('depositParadoxChart', {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Cancellation Rate (%)',
          data: rates,
          backgroundColor: ['#6366f1', '#ef4444', '#10b981'],
          borderRadius: 8
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterBody: (ctx) => {
                if (ctx[0].label === 'Non Refund') {
                  return 'Key Finding: 99.36% rate due to tour group block contracts defaulting in bulk.';
                }
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#94a3b8', callback: v => v + '%' },
            max: 100
          },
          y: { grid: { display: false }, ticks: { color: '#94a3b8' } }
        }
      }
    });
  }

  // Chart 5: Behavioral Dampeners & Catalysts (Radar Chart)
  function renderDriversRadarChart() {
    getOrCreateChart('driversRadarChart', {
      type: 'radar',
      data: {
        labels: [
          'Lead Time (>90d)',
          'OTA Distribution',
          'Price Elasticity (>€120)',
          'Room Reassignment Benefit',
          'Loyalty/Repeat Guest',
          'High Special Requests (2+)'
        ],
        datasets: [{
          label: 'Relative Impact Weight on Cancellation',
          data: [92, 75, 68, 15, 20, 25],
          backgroundColor: 'rgba(99, 102, 241, 0.25)',
          borderColor: '#6366f1',
          pointBackgroundColor: '#8b5cf6',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: '#8b5cf6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8' } }
        },
        scales: {
          r: {
            angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
            grid: { color: 'rgba(255, 255, 255, 0.08)' },
            pointLabels: { color: '#cbd5e1', font: { size: 11, weight: '600' } },
            ticks: { display: false }
          }
        }
      }
    });
  }

  // Chart 6: Top Feeder Countries Rate
  function renderCountryChart() {
    const countries = data.top_countries.slice(0, 8);
    getOrCreateChart('countryChart', {
      type: 'bar',
      data: {
        labels: countries.map(c => c.country),
        datasets: [{
          label: 'Cancellation Rate (%)',
          data: countries.map(c => c.cancel_rate),
          backgroundColor: countries.map(c => c.cancel_rate > 35 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(59, 130, 246, 0.7)'),
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#94a3b8', callback: v => v + '%' },
            max: 60
          }
        }
      }
    });
  }

  // Feature Importance Ranked List Rendering
  function renderFeatureImportance() {
    const container = document.getElementById('featureImportanceList');
    if (!container) return;

    container.innerHTML = data.feature_importance.map((item, idx) => {
      const pct = (item.importance * 100).toFixed(1);
      return `
        <div class="fi-item">
          <div class="fi-meta">
            <span class="fi-name">
              <span style="color: #6366f1; font-weight: 700;">#${idx + 1}</span> 
              ${item.feature}
            </span>
            <span class="fi-score">${(item.importance).toFixed(4)} (${pct}%)</span>
          </div>
          <div class="fi-bar-bg">
            <div class="fi-bar-fill" style="width: ${pct * 3.5}%;"></div>
          </div>
          <p class="fi-desc">${item.description}</p>
        </div>
      `;
    }).join('');
  }

  // Interactive Live Risk Calculator (Simulates ML scoring weights)
  function initRiskSimulator() {
    const leadInput = document.getElementById('simLeadTime');
    const adrInput = document.getElementById('simAdr');
    const depositSelect = document.getElementById('simDeposit');
    const channelSelect = document.getElementById('simChannel');
    const requestsSelect = document.getElementById('simRequests');
    const upgradeSelect = document.getElementById('simUpgrade');
    const repeatSelect = document.getElementById('simRepeat');

    const leadDisplay = document.getElementById('simLeadVal');
    const adrDisplay = document.getElementById('simAdrVal');
    const scoreDisplay = document.getElementById('simScoreDisplay');
    const badge = document.getElementById('simRiskBadge');
    const recText = document.getElementById('simRecommendationText');
    const gaugeCircle = document.getElementById('gaugeCircleSvg');

    function calculateRisk() {
      const lead = parseInt(leadInput.value, 10);
      const adr = parseFloat(adrInput.value);
      const deposit = depositSelect.value;
      const channel = channelSelect.value;
      const requests = parseInt(requestsSelect.value, 10);
      const isUpgraded = upgradeSelect.value === 'yes';
      const isRepeat = repeatSelect.value === 'yes';

      leadDisplay.textContent = `${lead} days`;
      adrDisplay.textContent = `€${adr}`;

      // Baseline probability ~35%
      let riskScore = 35;

      // 1. Lead Time factor
      if (lead <= 7) riskScore -= 22;
      else if (lead <= 30) riskScore -= 8;
      else if (lead > 180) riskScore += 28;
      else if (lead > 90) riskScore += 16;

      // 2. Deposit factor (Crucial finding)
      if (deposit === 'Non Refund') {
        riskScore = Math.max(riskScore, 94); // Virtually guaranteed default rate
      } else if (deposit === 'Refundable') {
        riskScore -= 12;
      }

      // 3. Distribution Channel
      if (channel === 'Online TA') riskScore += 8;
      else if (channel === 'Direct') riskScore -= 14;
      else if (channel === 'Corporate') riskScore -= 12;

      // 4. ADR Sensitivity
      if (adr > 150) riskScore += 10;
      else if (adr < 70) riskScore -= 6;

      // 5. Special Requests Dampener
      if (requests === 0) riskScore += 8;
      else if (requests === 1) riskScore -= 10;
      else if (requests >= 2) riskScore -= 22;

      // 6. Upgrades / Mismatch
      if (isUpgraded) riskScore -= 25;

      // 7. Repeated guest
      if (isRepeat) riskScore -= 18;

      // Clamp between 3% and 99%
      riskScore = Math.max(3, Math.min(99, Math.round(riskScore)));

      // Render score
      scoreDisplay.textContent = `${riskScore}%`;

      // Update Gauge SVG stroke-dashoffset (circumference = 2 * PI * 65 ≈ 408)
      const circumference = 408;
      const offset = circumference - (riskScore / 100) * circumference;
      gaugeCircle.style.strokeDashoffset = offset;

      // Style badge & recommendations
      if (riskScore >= 60) {
        gaugeCircle.style.stroke = '#ef4444';
        badge.className = 'risk-level-badge risk-high';
        badge.textContent = 'HIGH CANCELLATION HAZARD';
        recText.innerHTML = '<strong>Action Required:</strong> Overbooking hedge needed. Trigger proactive pre-arrival WhatsApp/email confirmation, offer complimentary meal voucher or room tier guarantee to lock guest in.';
      } else if (riskScore >= 30) {
        gaugeCircle.style.stroke = '#f59e0b';
        badge.className = 'risk-level-badge risk-medium';
        badge.textContent = 'MODERATE ATTRITION RISK';
        recText.innerHTML = '<strong>Action Recommended:</strong> Monitor booking status 14 days prior to arrival. Send itinerary customization prompts to increase guest investment.';
      } else {
        gaugeCircle.style.stroke = '#10b981';
        badge.className = 'risk-level-badge risk-low';
        badge.textContent = 'LOW HAZARD / HIGH STICKINESS';
        recText.innerHTML = '<strong>Secure Reservation:</strong> High probability of arrival. Ideal candidate for upsell packages (spa, dining, airport transfer) without fear of cancellation.';
      }
    }

    [leadInput, adrInput, depositSelect, channelSelect, requestsSelect, upgradeSelect, repeatSelect].forEach(el => {
      el.addEventListener('input', calculateRisk);
      el.addEventListener('change', calculateRisk);
    });

    calculateRisk();
  }

  // Sample Bookings Data Table
  function renderBookingsTable() {
    const tbody = document.getElementById('bookingsTableBody');
    const searchInput = document.getElementById('tableSearchInput');
    const hotelFilter = document.getElementById('tableHotelFilter');
    const statusFilter = document.getElementById('tableStatusFilter');

    if (!tbody) return;

    function populateTable() {
      const search = (searchInput ? searchInput.value.toLowerCase() : '');
      const hFilter = (hotelFilter ? hotelFilter.value : 'ALL');
      const sFilter = (statusFilter ? statusFilter.value : 'ALL');

      const filtered = data.sample_bookings.filter(row => {
        const matchesSearch = search === '' || 
          row.country.toLowerCase().includes(search) || 
          row.booking_id.toString().includes(search) ||
          row.distribution_channel.toLowerCase().includes(search);

        const matchesHotel = hFilter === 'ALL' || row.hotel === hFilter;
        const matchesStatus = sFilter === 'ALL' || 
          (sFilter === 'Canceled' && row.is_canceled === 1) ||
          (sFilter === 'Confirmed' && row.is_canceled === 0);

        return matchesSearch && matchesHotel && matchesStatus;
      });

      tbody.innerHTML = filtered.slice(0, 50).map(row => {
        const isCanceled = row.is_canceled === 1;
        const badge = isCanceled 
          ? '<span class="status-badge status-canceled">Canceled</span>' 
          : '<span class="status-badge status-confirmed">Confirmed</span>';
        
        return `
          <tr>
            <td><strong>#${row.booking_id}</strong></td>
            <td>${row.hotel}</td>
            <td>${badge}</td>
            <td>${row.lead_time} d</td>
            <td>${row.arrival_date_month} ${row.arrival_date_year}</td>
            <td>€${row.adr}</td>
            <td>${row.deposit_type}</td>
            <td>${row.distribution_channel}</td>
            <td><span style="font-weight:700;">${row.country || 'N/A'}</span></td>
            <td>${row.total_of_special_requests}</td>
            <td>${row.room_type_mismatch === 1 ? '<span style="color:#34d399">Upgraded</span>' : 'Standard'}</td>
          </tr>
        `;
      }).join('');
    }

    if (searchInput) searchInput.addEventListener('input', populateTable);
    if (hotelFilter) hotelFilter.addEventListener('change', populateTable);
    if (statusFilter) statusFilter.addEventListener('change', populateTable);

    populateTable();
  }
});
