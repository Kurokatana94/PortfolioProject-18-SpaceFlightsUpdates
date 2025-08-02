document.addEventListener("DOMContentLoaded", () => {
    const raw = window.rawData || [];
    const upcoming = window.upcomingLaunches || [];
    const ctx = document.getElementById('launchChart')?.getContext('2d');
    let chart;

    // Set default start/end before initializing flatpickr
    const today = new Date();
    const endDate = new Date(today.getFullYear(), today.getMonth(), 1); // current month
    const startDate = new Date(today.getFullYear(), today.getMonth() - 11, 1); // 11 months back

    // Flatpickr with monthSelectPlugin
    const startPicker = flatpickr("#startMonth", {
        dateFormat: "Y-m",
        altFormat: "F Y",
        altInput: true,
        plugins: [new monthSelectPlugin({ shorthand: true })]
    });

    const endPicker = flatpickr("#endMonth", {
        dateFormat: "Y-m",
        altFormat: "F Y",
        altInput: true,
        plugins: [new monthSelectPlugin({ shorthand: true })]
    });

    // Set the values via Flatpickr API (not just .value!)
    startPicker.setDate(startDate, true); // true = trigger change
    endPicker.setDate(endDate, true);

    flatpickr("#startMonth", {
        dateFormat: "Y-m",
        altFormat: "F Y",
        altInput: true,
        plugins: [new monthSelectPlugin({ shorthand: true })]
    });

    flatpickr("#endMonth", {
        dateFormat: "Y-m",
        altFormat: "F Y",
        altInput: true,
        plugins: [new monthSelectPlugin({ shorthand: true })]
    });

    // === Helpers ===
    function getDateRange(startStr, endStr) {
        const start = new Date(startStr + "-01");
        const end = new Date(endStr + "-01");
        const months = [];
        while (start <= end) {
            months.push(start.toISOString().slice(0, 7)); // 'YYYY-MM'
            start.setMonth(start.getMonth() + 1);
        }
        return months;
    }

    function groupLaunches(data, granularity = 'month') {
        const counts = {};
        data.forEach(launch => {
            const dateStr = launch.Date || launch.date;
            if (!dateStr) return;

            const key = granularity === 'year' ? dateStr.slice(0, 4) : dateStr.slice(0, 7); // YYYY or YYYY-MM

            if (!counts[key]) counts[key] = { total: 0, success: 0, failure: 0, partial: 0 };
            counts[key].total++;

            const status = (launch.Status || '').toLowerCase();
            if (status.includes('success')) counts[key].success++;
            else if (status.includes('failure')) counts[key].failure++;
            else if (status.includes('partial')) counts[key].partial++;
        });
        return counts;
    }

    function updateChart(start, end) {
        const startDate = new Date(start + "-01");
        const endDate = new Date(end + "-01");
        const diffInMonths = (endDate.getFullYear() - startDate.getFullYear()) * 12 + (endDate.getMonth() - startDate.getMonth()) + 1;

        const useYearly = diffInMonths > 25;
        const granularity = useYearly ? 'year' : 'month';
        const labels = [];

        if (useYearly) {
            const startYear = parseInt(start.slice(0, 4), 10);
            const endYear = parseInt(end.slice(0, 4), 10);
            for (let y = startYear; y <= endYear; y++) {
                labels.push(String(y));
            }
        } else {
            const range = getDateRange(start, end);
            labels.push(...range);
        }

        const grouped = groupLaunches(raw, granularity);

        const total = [], success = [], failure = [], partial = [];

        labels.forEach(label => {
            const stats = grouped[label] || {};
            total.push(stats.total || 0);
            success.push(stats.success || 0);
            failure.push(stats.failure || 0);
            partial.push(stats.partial || 0);
        });

        chart.data.labels = labels;
        chart.data.datasets[0].data = total;
        chart.data.datasets[1].data = success;
        chart.data.datasets[2].data = failure;
        chart.data.datasets[3].data = partial;
        chart.update();
    }

    if (ctx) {
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Total', data: [], borderColor: '#1E90FF', borderDash: [5, 5], fill: false },
                    { label: 'Success', data: [], borderColor: '#32CD32', borderDash: [5, 5], fill: false },
                    { label: 'Failure', data: [], borderColor: '#DC143C', borderDash: [5, 5], fill: false },
                    { label: 'Partial', data: [], borderColor: '#FFA500', borderDash: [5, 5], fill: false }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // Default to last 12 months
        const today = new Date();
        const end = today.toISOString().slice(0, 7);
        const startDate = new Date(today.getFullYear(), today.getMonth() - 11, 1);
        const start = startDate.toISOString().slice(0, 7);

        document.getElementById('startMonth').value = start;
        document.getElementById('endMonth').value = end;
        updateChart(start, end);

        // On custom range submit
        document.getElementById('rangeForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const start = document.getElementById('startMonth').value;
            const end = document.getElementById('endMonth').value;
            if (start && end && start <= end) {
                updateChart(start, end);
            } else {
                alert('Please enter a valid date range.');
            }
        });
    }

    // === FullCalendar (same as before) ===
    const formatEvent = (launch, isFuture = false) => {
        const dateISO = launch.Date || launch.date || launch.date_str;
        const date = dateISO?.slice(0, 10);

        let color;
        if (isFuture) {
            color = 'blue';
        } else {
            const status = (launch.Status || launch.status || '').toLowerCase();
            if (status.includes('launch successful')) color = 'green';
            else if (status.includes('launch failure')) color = 'red';
            else color = 'orange';
        }

        return {
            title: launch.Name || '',
            start: date,
            allDay: true,
            extendedProps: {
                color,
                provider: launch.Provider || '',
                location: launch.Location || '',
                status: launch.Status || ''
            }
        };
    };

    const events = [
        ...raw.map(l => formatEvent(l, false)),
        ...upcoming.map(l => formatEvent(l, true))
    ];

    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            events,
            eventContent: function(arg) {
                const color = arg.event.extendedProps.color;
                const name = arg.event.title || 'Launch';
                const provider = arg.event.extendedProps.provider || 'Unknown';
                const location = arg.event.extendedProps.location || 'Unknown';
                const status = arg.event.extendedProps.status || 'Unknown';

                const dot = document.createElement('div');
                dot.className = 'launch-dot';
                dot.style.backgroundColor = color;
                dot.title = `${name}\nProvider: ${provider}\nLocation: ${location}\nStatus: ${status}`;

                const container = document.createElement('div');
                container.className = 'launch-container';
                container.appendChild(dot);

                return { domNodes: [container] };
            }
        });
        calendar.render();
    }
});
