document.addEventListener("DOMContentLoaded", () => {
    const chartData = window.chartData;
    const upcoming = window.upcomingLaunches || [];
    const raw = window.rawData || [];

    // === Chart.js Setup ===
    const ctx = document.getElementById('launchChart')?.getContext('2d');
    if (ctx && chartData) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.years,
                datasets: [
                    { label: 'Total', data: chartData.total, borderColor: 'blue', fill: false },
                    { label: 'Success', data: chartData.success, borderColor: 'green', fill: false },
                    { label: 'Failure', data: chartData.failure, borderColor: 'red', fill: false },
                    { label: 'Partial', data: chartData.partial, borderColor: 'orange', fill: false }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // === Merge Data ===
    const formatEvent = (launch, isFuture = false) => {
        const dateISO = launch.Date || launch.date || launch.date_str;
        const date = dateISO?.slice(0, 10); // 'YYYY-MM-DD'

        let color;
        if (isFuture) {
            color = 'blue';
        } else {
            const status = (launch.Status || launch.status || '').toLowerCase();
            if (status.includes('launch successful')) color = 'green';
            else if (status.includes('launch failure')) color = 'red';
            else if (status.includes('')) color = 'orange';
            else color = 'gray'; // fallback
        }

        return {
            start: date,
            allDay: true,
            extendedProps: { color }
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

                const dot = document.createElement('div');
                dot.className = 'launch-dot';
                dot.style.backgroundColor = color;

                const container = document.createElement('div');
                container.className = 'launch-container';
                container.appendChild(dot);

                return { domNodes: [container] };
            }
        });
        calendar.render();
    }
});
