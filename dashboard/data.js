let allData = [];
let currentPage = 1;
const rowsPerPage = 100;

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('all_cleaned_data.json');
        if (!response.ok) throw new Error('Failed to load data');
        
        allData = await response.json();
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('table-container').style.display = 'block';
        document.getElementById('pagination').style.display = 'flex';
        document.getElementById('record-count').innerText = `${allData.length.toLocaleString()} total records loaded`;
        
        renderPage(currentPage);
    } catch (e) {
        document.getElementById('loading').innerHTML = `<p style="color:red;">Error loading data: ${e.message}</p>`;
    }

    document.getElementById('prevBtn').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage(currentPage);
        }
    });

    document.getElementById('nextBtn').addEventListener('click', () => {
        if (currentPage < Math.ceil(allData.length / rowsPerPage)) {
            currentPage++;
            renderPage(currentPage);
        }
    });
});

function renderPage(page) {
    const totalPages = Math.ceil(allData.length / rowsPerPage);
    document.getElementById('pageInfo').innerText = `Page ${page.toLocaleString()} of ${totalPages.toLocaleString()}`;
    
    document.getElementById('prevBtn').disabled = page === 1;
    document.getElementById('nextBtn').disabled = page === totalPages;

    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const pageData = allData.slice(start, end);

    const tbody = document.getElementById('data-tbody');
    tbody.innerHTML = pageData.map(r => `
        <tr>
            <td style="white-space:nowrap;">${r.date || '-'}</td>
            <td>${r.rating ? r.rating + '★' : '-'}</td>
            <td><span class="badge">${r.source}</span></td>
            <td style="color:#334155;">${r.text}</td>
        </tr>
    `).join('');
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
