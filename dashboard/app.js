document.addEventListener('DOMContentLoaded', async () => {
    try {
        let d = null;
        // Check if Firebase is initialized and available
        if (typeof firebase !== 'undefined') {
            try {
                const db = firebase.firestore();
                const docRef = db.collection("analytics").doc("latest");
                const docSnap = await docRef.get();
                if (docSnap.exists) {
                    d = docSnap.data();
                    console.log("Loaded data from Firebase Firestore");
                } else {
                    console.warn("No 'latest' document in 'analytics' collection. Falling back to local file.");
                }
            } catch (fbError) {
                console.warn("Firebase fetch failed, falling back to local file.", fbError);
            }
        }
        
        // Fallback to local file if Firebase fails or is not available
        if (!d) {
            const t = '?t=' + Date.now();
            const response = await fetch('analytics.json' + t);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            d = await response.json();
            console.log("Loaded data from local analytics.json");
        }

        // ── KPIs ───────────────────────────────────────────────────────────
        const ps = d.pipeline_summary;
        const sent = d.sentiment;
        if (!sent) throw new Error("Sentiment data is missing from analytics.json!");
        const negCount = sent.negative || ps.negative_reviews || 0;
        const posCount = sent.positive || ps.positive_reviews || 0;
        const neuCount = sent.neutral  || ps.neutral_reviews  || 0;
        const total    = posCount + neuCount + negCount;
        const sourcesStr = Object.entries(d.sources).map(([k,v]) => `${k.split(' ')[0]}: ${v.toLocaleString()}`).join(' · ');

        document.getElementById('kpi-raw').innerText          = (ps.total_raw || 0).toLocaleString();
        document.getElementById('kpi-sources-note').innerText = sourcesStr;
        document.getElementById('kpi-clean').innerText        = (ps.total_cleaned || 0).toLocaleString();
        document.getElementById('kpi-clean-pct').innerText    = `${(((ps.total_cleaned||0)/(ps.total_raw||1))*100).toFixed(1)}% of raw`;
        document.getElementById('kpi-neg').innerText          = negCount.toLocaleString();
        document.getElementById('kpi-neg-pct').innerText      = `${((negCount/total)*100).toFixed(1)}% of reviews`;
        document.getElementById('kpi-pos').innerText          = posCount.toLocaleString();
        document.getElementById('kpi-pos-pct').innerText      = `${((posCount/total)*100).toFixed(1)}% of reviews`;
        document.getElementById('kpi-opp').innerText          = ps.opportunities_found || 0;

        // Update rating badge dynamically
        const ratingBadge = document.querySelector('#ratingChart')?.closest('.card')?.querySelector('.badge');
        if (ratingBadge) ratingBadge.innerText = `${(ps.total_cleaned||0).toLocaleString()} reviews`;

        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#64748b';

        // ── SOURCE DONUT ───────────────────────────────────────────────────
        const srcLabels  = Object.keys(d.sources);
        const srcValues  = Object.values(d.sources);
        const srcColors  = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
        const srcTotal   = srcValues.reduce((a,b)=>a+b, 0);
        document.getElementById('donut-total').innerText = srcTotal.toLocaleString();

        new Chart(document.getElementById('sourceChart'), {
            type: 'doughnut',
            data: { labels: srcLabels, datasets: [{ data: srcValues, backgroundColor: srcColors, borderWidth: 2, borderColor: '#fff' }] },
            options: { cutout: '72%', plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toLocaleString()}` } } }, responsive: true, maintainAspectRatio: false }
        });

        const srcLegend = document.getElementById('sourceLegend');
        srcLabels.forEach((l, i) => {
            const pct = ((srcValues[i]/srcTotal)*100).toFixed(1);
            srcLegend.innerHTML += `<div class="legend-row"><div class="legend-label"><div class="dot" style="background:${srcColors[i]}"></div>${l}</div><div class="legend-val">${srcValues[i].toLocaleString()} (${pct}%)</div></div>`;
        });

        // ── RATING BAR ─────────────────────────────────────────────────────
        const rd = d.rating_distribution;
        new Chart(document.getElementById('ratingChart'), {
            type: 'bar',
            data: {
                labels: rd.labels.map(l => l + ' ★'),
                datasets: [{
                    data: rd.values,
                    backgroundColor: ['#ef4444','#f59e0b','#94a3b8','#10b981','#3b82f6'],
                    borderRadius: 4
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { grid: { color: '#f1f5f9' }, border: { display: false }, ticks: { callback: v => v >= 1000 ? (v/1000).toFixed(0)+'k' : v } }, x: { grid: { display: false }, border: { display: false } } },
                responsive: true, maintainAspectRatio: false
            }
        });

        // ── USER SEGMENT DONUT ────────────────────────────────────────────────
        const segs = d.user_segments || [];
        const segColors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899', '#14b8a6', '#f97316'];
        const segLabels = segs.map(s => s.name);
        const segValues = segs.map(s => s.count);
        
        if (segs.length > 0) {
            document.getElementById('segment-pct').innerText = segs[0].percentage + '%';
        }

        new Chart(document.getElementById('segmentChart'), {
            type: 'doughnut',
            data: { labels: segLabels, datasets: [{ data: segValues, backgroundColor: segColors, borderWidth: 2, borderColor: '#fff' }] },
            options: { cutout: '72%', plugins: { legend: { display: false } }, responsive: true, maintainAspectRatio: false }
        });

        const segLegend = document.getElementById('segmentLegend');
        segs.forEach((s, i) => {
            segLegend.innerHTML += `<div class="legend-row"><div class="legend-label"><div class="dot" style="background:${segColors[i]}"></div>${s.name}</div><div class="legend-val">${s.count.toLocaleString()} (${s.percentage}%)</div></div>`;
        });

        // ── BLOCKERS TABLE ─────────────────────────────────────────────────
        const tbody = document.querySelector('#blockers-table tbody');
        const maxCount = d.top_complaint_blockers[0]?.count || 1;
        d.top_complaint_blockers.forEach((b, i) => {
            const barWidth = (b.count / maxCount * 100).toFixed(0);
            tbody.innerHTML += `
                <tr>
                    <td><span class="rank-badge">${i+1}</span></td>
                    <td><strong>${b.blocker}</strong></td>
                    <td>${b.count.toLocaleString()}</td>
                    <td>${b.percentage}%</td>
                    <td><div class="mini-bar-wrap"><div class="mini-bar" style="width:${barWidth}%"></div></div></td>
                </tr>`;
        });

        // ── WISHLIST BEHAVIORS TABLE (PHASE 3) ─────────────────────────────
        const relBody = document.querySelector('#relevant-table tbody');
        const wishlistBehaviors = d.wishlist_behaviors || [];
        
        if (wishlistBehaviors.length === 0) {
            relBody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#64748b;">No Phase 3 data found.</td></tr>`;
        } else {
            const maxWishlistCount = wishlistBehaviors[0]?.count || 1;
            wishlistBehaviors.forEach((w, i) => {
                const barWidth = (w.count / maxWishlistCount * 100).toFixed(0);
                relBody.innerHTML += `
                    <tr>
                        <td><span class="rank-badge">${i+1}</span></td>
                        <td><strong>${w.category}</strong></td>
                        <td>${w.count.toLocaleString()}</td>
                        <td>${w.percentage}%</td>
                        <td><div class="mini-bar-wrap"><div class="mini-bar" style="width:${barWidth}%"></div></div></td>
                    </tr>`;
            });
        }

        // ── POSTPONED PURCHASE TABLE ───────────────────────────────────────
        const postBody = document.querySelector('#postponed-table tbody');
        const postponedReasons = d.postponed_reasons || [];
        
        if (postponedReasons.length === 0) {
            postBody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#64748b;">No data found.</td></tr>`;
        } else {
            const maxPostCount = postponedReasons[0]?.count || 1;
            postponedReasons.forEach((p, i) => {
                const barWidth = (p.count / maxPostCount * 100).toFixed(0);
                postBody.innerHTML += `
                    <tr>
                        <td><span class="rank-badge">${i+1}</span></td>
                        <td><strong>${p.reason}</strong></td>
                        <td>${p.count.toLocaleString()}</td>
                        <td>${p.percentage}%</td>
                        <td><div class="mini-bar-wrap"><div class="mini-bar" style="width:${barWidth}%; background:#ef4444"></div></div></td>
                    </tr>`;
            });
        }



        // ── INFO SEEKING & JOURNEYS ─────────────────────────────────────────
        const infoList = document.getElementById('info-seeking-list');
        const infos = d.external_info_seeking || [];
        infoList.innerHTML = infos.map(inf => `
            <div class="info-row">
                <div class="info-plat">
                    <span class="info-icon">${inf.icon}</span>
                    <strong>${inf.platform}</strong>
                </div>
                <div class="info-reason">${inf.reason}</div>
                <div class="info-pct">${inf.percentage}%</div>
            </div>
        `).join('');

        const journeyContainer = document.getElementById('journey-container');
        const journeys = d.user_journeys || [];
        journeyContainer.innerHTML = journeys.map(j => `
            <div class="journey-card">
                <div class="journey-hdr">
                    <strong>${j.name}</strong>
                    <span class="journey-pct">${j.percentage}% of users</span>
                </div>
                <div class="journey-flow">
                    ${j.steps.map((step, idx) => `
                        <div class="journey-step">${step}</div>
                        ${idx < j.steps.length - 1 ? `<div class="journey-arrow">➔</div>` : ''}
                    `).join('')}
                </div>
            </div>
        `).join('');

        // ── OPPORTUNITIES ──────────────────────────────────────────────────
        const oppContainer = document.getElementById('opp-container');
        const opps = d.opportunities || [];
        if (opps.length === 0) {
            oppContainer.innerHTML = `
                <div class="no-opp">
                    <p>No opportunities scored yet. Run the full pipeline to discover insights.</p>
                    <p><code>python main.py --from-phase 4</code></p>
                </div>`;
        } else {
            // Use the order exactly as provided in analytics.json

            opps.forEach(opp => {
                const relLabel = opp.metric_relevance ?? opp.scores?.metric_relevance ?? 'Medium';
                
                let freq = opp.frequency_score_override ?? opp.scores?.frequency ?? opp.frequency_score ?? 0;
                if (freq <= 1 && opp.frequency_score_override === undefined) freq = freq * 100; // e.g. 0.071 -> 7.1 out of 10
                if (freq > 10) freq = 10; // Cap at 10
                
                let sev = opp.severity_score_override ?? opp.scores?.severity ?? opp.severity_avg ?? 0;
                if (sev <= 5 && opp.severity_score_override === undefined) sev = sev * 2; // e.g. 2.5/5 -> 5/10
                
                let relScore = opp.metric_relevance_score_override ?? 5.0;
                if (opp.metric_relevance_score_override === undefined) {
                    if (relLabel === 'High') relScore = 9.0;
                    else if (relLabel === 'Medium') relScore = 6.0;
                    else if (relLabel === 'Low') relScore = 3.0;
                }
                
                let evScore = opp.evidence_score_override ?? 5.0;
                if (opp.evidence_score_override === undefined) {
                    const evLabel = opp.evidence_strength ?? opp.scores?.evidence_strength ?? '';
                    if (evLabel === 'Cross-source') evScore = 8.5;
                    else if (evLabel === 'Multi-source') evScore = 7.0;
                    else if (evLabel === 'Single-source') evScore = 4.0;
                }
                
                const quotes= opp.representative_quotes || [];
                const quotesHTML = quotes.slice(0, 3).map(q => `<div class="opp-quote">${q}</div>`).join('');

                oppContainer.innerHTML += `
                    <div class="opp-card">
                        <div>
                            <div class="opp-name">${opp.name}</div>
                            <div class="opp-desc">${opp.opportunity_statement}</div>
                            <div style="margin-top:0.75rem"><span class="opp-badge ${relLabel.toLowerCase()}">${relLabel} Priority</span></div>
                            ${quotesHTML.length ? `<div class="opp-quotes" style="margin-top:1rem">${quotesHTML}</div>` : ''}
                        </div>
                        <div class="opp-scores">
                            ${scoreRow10('Frequency', freq, '#3b82f6')}
                            ${scoreRow10('Severity', sev, '#ef4444')}
                            ${scoreRow10('Metric Relevance', relScore, '#8b5cf6')}
                            ${scoreRow10('Evidence', evScore, '#10b981')}
                        </div>
                    </div>`;
            });
        }
    } catch (e) {
        console.error("Dashboard failed to load:", e);
        alert("CRASH: " + e.message);
    }
});

// Helper to render a score bar row out of 10
function scoreRow10(label, val, color) {
    if (val === 'Insufficient evidence' || val === null || val === undefined) {
        return `
            <div class="score-row">
                <span class="score-label">${label}</span>
                <div class="score-bar-wrap"><div class="score-bar" style="width:0%;background:#e2e8f0"></div></div>
                <span class="score-value" style="color:#94a3b8;font-size:0.75rem;white-space:nowrap;">Insufficient evidence</span>
            </div>`;
    }
    const v = Math.min(10, Math.max(0, val));
    const p = (v / 10) * 100;
    return `
        <div class="score-row">
            <span class="score-label">${label}</span>
            <div class="score-bar-wrap"><div class="score-bar" style="width:${p.toFixed(0)}%;background:${color}"></div></div>
            <span class="score-value" style="color:${color}">${v.toFixed(1)}/10</span>
        </div>`;
}

// Export Report
function exportReport() {
    window.open('../reports/output/discovery_report_' + new Date().toISOString().slice(0,10) + '.md', '_blank');
}
