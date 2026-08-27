document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('discovery-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnIcon = submitBtn.querySelector('.btn-icon');
    const spinner = submitBtn.querySelector('.spinner');
    
    // Status Trackers
    const statusSteps = {
        discovery: document.getElementById('step-discovery'),
        signals: document.getElementById('step-signals'),
        companies: document.getElementById('step-companies'),
        execs: document.getElementById('step-execs'),
        contacts: document.getElementById('step-contacts')
    };

    // Stat Trackers
    const stats = {
        signals: document.getElementById('stat-signals'),
        companies: document.getElementById('stat-companies'),
        people: document.getElementById('stat-people'),
        contacts: document.getElementById('stat-contacts')
    };

    // Containers
    const containers = {
        signals: document.getElementById('signals-container'),
        companies: document.getElementById('companies-container'),
        people: document.getElementById('people-container')
    };

    function resetUI() {
        Object.values(statusSteps).forEach(el => {
            el.className = 'step pending';
        });
        Object.values(stats).forEach(el => {
            el.textContent = '0';
        });
        Object.values(containers).forEach(el => {
            el.innerHTML = '';
        });
    }

    function setStepStatus(stepKey, status) {
        statusSteps[stepKey].className = `step ${status}`;
    }
    
    // Helper to generate a signal card
    function renderSignal(signal) {
        return `
            <div class="card">
                <div class="card-header">
                    <div class="card-title">${signal.company_name}</div>
                    <div class="card-badge">${signal.signal_type}</div>
                </div>
                <div class="card-body">
                    <p><strong>Location:</strong> ${signal.location || 'N/A'}</p>
                    <p>${signal.title || 'Signal discovered'}</p>
                </div>
            </div>
        `;
    }

    // Helper to generate a company card
    function renderCompany(company) {
        return `
            <div class="card">
                <div class="card-header">
                    <div class="card-title">${company.name}</div>
                    <div class="card-badge">Enriched</div>
                </div>
                <div class="card-body">
                    <p><strong>Domain:</strong> ${company.domain || 'N/A'}</p>
                    <p><strong>Industry:</strong> ${company.industry || 'N/A'}</p>
                </div>
            </div>
        `;
    }

    function renderContactRows(contacts) {
        let contactHtml = '';
        if (contacts && contacts.length > 0) {
            contacts.forEach(c => {
                contactHtml += `
                    <div class="contact-row">
                        <i data-lucide="${c.contact_type === 'email' ? 'mail' : 'phone'}"></i>
                        <span>${c.contact_value}</span>
                        ${c.confidence ? `<span style="color:var(--text-muted); font-size:10px;">(${Math.round(c.confidence*100)}%)</span>` : ''}
                    </div>
                `;
            });
        }
        return contactHtml || '<p class="contact-hint">No contact found yet.</p>';
    }

    // Helper to generate an executive card. Contact discovery is deliberately
    // initiated by the card button, never while rendering the waterfall.
    function renderPerson(person) {
        const contactButton = `
            <div class="contact-actions">
                <button type="button" class="btn-contact" data-person-id="${person.person_id}">
                    <i data-lucide="search"></i>
                    Find public contact
                </button>
                <span class="contact-hint">Runs only when requested</span>
            </div>
            <div class="contact-results" data-contact-results-for="${person.person_id}"></div>
        `;

        return `
            <div class="card person-card" data-person-card="${person.person_id}">
                <div class="card-header">
                    <div class="card-title">${person.full_name}</div>
                    <div class="card-badge" style="background: rgba(0, 210, 255, 0.1); color: var(--accent-secondary);">${person.current_title || 'Exec'}</div>
                </div>
                <div class="card-body">
                    <p><strong>Location:</strong> ${person.location || 'N/A'}</p>
                    ${person.linkedin_url ? `<p><a href="${person.linkedin_url}" target="_blank" style="color:var(--accent-secondary)">LinkedIn Profile</a></p>` : ''}
                    ${contactButton}
                </div>
            </div>
        `;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Prepare request
        const location = document.getElementById('location').value;
        const signalCheckboxes = document.querySelectorAll('input[name="signal"]:checked');
        const signalTypes = Array.from(signalCheckboxes).map(cb => cb.value);

        const payload = {
            location: location,
            signal_types: signalTypes.length ? signalTypes : ['commercial_property_requirement']
        };

        // UI Loading State
        submitBtn.disabled = true;
        btnText.textContent = 'Running waterfall...';
        btnIcon.classList.add('hidden');
        spinner.classList.remove('hidden');
        
        resetUI();
        
        // Simulate progress since backend is currently synchronous
        // In a real prod environment with webhooks/websockets, this would be real-time
        setStepStatus('discovery', 'active');
        
        // Progress simulation intervals
        let progressTimers = [];
        progressTimers.push(setTimeout(() => { setStepStatus('discovery', 'completed'); setStepStatus('signals', 'active'); }, 2000));
        progressTimers.push(setTimeout(() => { setStepStatus('signals', 'completed'); setStepStatus('companies', 'active'); }, 4000));
        progressTimers.push(setTimeout(() => { setStepStatus('companies', 'completed'); setStepStatus('execs', 'active'); }, 6000));

        try {
            const response = await fetch('/api/discover', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            
            // Clear simulated timers
            progressTimers.forEach(t => clearTimeout(t));
            
            // The waterfall completes at people storage. Contacts remain
            // pending until a person explicitly requests contact discovery.
            ['discovery', 'signals', 'companies', 'execs'].forEach(k => setStepStatus(k, 'completed'));
            setStepStatus('contacts', 'pending');

            if (data.status === 'success' && data.results) {
                const res = data.results;
                
                // Update stats
                stats.signals.textContent = res.signals_extracted || 0;
                stats.companies.textContent = res.companies_processed || 0;
                stats.people.textContent = res.people_discovered || 0;
                stats.contacts.textContent = res.contacts_found || 0;

                // Refresh once from the persisted DB state after the waterfall
                // completes. The UI does not render provider payloads directly.
                const stateResponse = await fetch(
                    `/api/discovery/state?location=${encodeURIComponent(location)}`
                );
                if (!stateResponse.ok) throw new Error('Could not load persisted discovery state');
                const state = await stateResponse.json();

                stats.signals.textContent = state.counts.signals;
                stats.companies.textContent = state.counts.companies;
                stats.people.textContent = state.counts.people;

                if (state.signals && state.signals.length > 0) {
                    containers.signals.innerHTML = '';
                    // Only show top 10
                    state.signals.slice(0, 10).forEach(s => {
                        containers.signals.innerHTML += renderSignal(s);
                    });
                } else {
                    containers.signals.innerHTML = '<div class="empty-state">No signals found in DB.</div>';
                }

                containers.companies.innerHTML = state.companies.length
                    ? state.companies.map(renderCompany).join('')
                    : '<div class="empty-state">No companies enriched.</div>';
                containers.people.innerHTML = state.people.length
                    ? state.people.map(renderPerson).join('')
                    : '<div class="empty-state">No people discovered.</div>';

                // Re-init lucide icons for newly added HTML
                lucide.createIcons();
            } else {
                alert('Pipeline returned error or no results.');
            }

        } catch (error) {
            console.error(error);
            alert('Failed to run pipeline. Check console.');
            Object.keys(statusSteps).forEach(k => setStepStatus(k, 'pending'));
        } finally {
            submitBtn.disabled = false;
            btnText.textContent = 'Run Discovery Waterfall';
            btnIcon.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    });

    // Explicit, per-person contact search action.
    containers.people.addEventListener('click', async (event) => {
        const button = event.target.closest('.btn-contact');
        if (!button) return;

        const personId = button.dataset.personId;
        const results = containers.people.querySelector(
            `[data-contact-results-for="${personId}"]`
        );
        button.disabled = true;
        button.classList.add('loading');
        button.innerHTML = '<span class="spinner"></span> Searching...';

        try {
            const response = await fetch(`/api/people/${personId}/discover-contact`, {
                method: 'POST'
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Contact search failed');

            const contactsResponse = await fetch(`/api/people/${personId}/contacts`);
            const contactsData = await contactsResponse.json();
            results.innerHTML = renderContactRows(contactsData.contacts || []);
            stats.contacts.textContent = String(
                Number(stats.contacts.textContent || 0) + (data.contact ? 1 : 0)
            );
        } catch (error) {
            results.innerHTML = `<p class="contact-error">${error.message}</p>`;
        } finally {
            button.disabled = false;
            button.classList.remove('loading');
            button.innerHTML = '<i data-lucide="search"></i> Find public contact';
            lucide.createIcons();
        }
    });
});
