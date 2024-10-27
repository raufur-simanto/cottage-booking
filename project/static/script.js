document.addEventListener('DOMContentLoaded', function() {
    const apiStatus = document.getElementById('apiStatus');
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');
    const availabilityFilter = document.getElementById('availabilityFilter');
    const cottageList = document.getElementById('cottageList');
    const preferredCitySelect = document.getElementById('preferredCity');

    const API_BASE = '/cottages';

    // List of cities (you can expand this list as needed)
    const cities = ['Helsinki', 'Tampere', 'Turku', 'Oulu', 'Espoo', 'Vantaa', 'Jyväskylä'];

    // Populate the preferred city dropdown
    cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        preferredCitySelect.appendChild(option);
    });

    // Check API status
    fetch(`${API_BASE}/alive`)
        .then(response => response.json())
        .then(data => {
            apiStatus.textContent = `API Status: ${data.msg}`;
            apiStatus.classList.add('active');
        })
        .catch(error => {
            apiStatus.textContent = 'API Status: Error - Not responding';
            console.error('Error checking API status:', error);
        });

    // Handle search form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(searchForm);
        const searchCriteria = {};

        formData.forEach((value, key) => {
            if (['requiredPlaces', 'requiredBedrooms', 'maxLakeDistance', 'maxCityDistance', 'numberOfDays', 'dateShift'].includes(key)) {
                // Convert to number for numeric fields
                searchCriteria[key] = parseInt(value, 10);
            } else if (key === 'startDate') {
                // Convert date to "dd.mm.yyyy" format
                const date = new Date(value);
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
                const year = date.getFullYear();
                searchCriteria[key] = `${day}.${month}.${year}`;
            } else {
                // For other fields (like bookerName and preferredCity), keep as string
                searchCriteria[key] = value;
            }
        });

        console.log('Search criteria:', searchCriteria); // Log the formatted search criteria

        fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchCriteria),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Search results:', data); // Log the search results
            displayCottages(data.results, searchResults);
        })
        .catch(error => {
            console.error('Error searching cottages:', error);
            searchResults.innerHTML = '<p>Error searching cottages. Please try again.</p>';
        });
    });

    // Handle availability filter change
    availabilityFilter.addEventListener('change', fetchAllCottages);

    // Fetch all cottages on page load
    fetchAllCottages();

    function fetchAllCottages() {
        const isAvailable = availabilityFilter.value;
        const url = `${API_BASE}/all${isAvailable ? `?isAvailable=${isAvailable}` : ''}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('Fetched cottages:', data);  // Log the fetched data
                displayCottages(data.results, cottageList);
            })
            .catch(error => {
                console.error('Error fetching cottages:', error);
                cottageList.innerHTML = '<p>Error fetching cottages. Please try again.</p>';
            });
    }

    function displayCottages(cottages, container) {
        console.log('Displaying cottages:', cottages);  // Log the cottages being displayed
        container.innerHTML = '';
        if (Array.isArray(cottages) && cottages.length > 0) {
            cottages.forEach(cottage => {
                const cottageElement = createCottageElement(cottage);
                container.appendChild(cottageElement);
            });
        } else {
            container.innerHTML = '<p>No cottages found.</p>';
        }
    }

    function createCottageElement(cottage) {
        const cottageElement = document.createElement('div');
        cottageElement.classList.add('cottage-item');
        
        const placeholderImage = `https://via.placeholder.com/300x200?text=${encodeURIComponent(cottage.cottageName)}`;
        
        // Create booking period HTML if it exists
        let bookingPeriodHtml = '';
        if (cottage.bookingPeriod && cottage.bookingPeriod.startDate && cottage.bookingPeriod.endDate) {
            bookingPeriodHtml = `
                <div class="booking-period">
                    <h4>Booking Period</h4>
                    <p>From: ${cottage.bookingPeriod.startDate}</p>
                    <p>To: ${cottage.bookingPeriod.endDate}</p>
                </div>
            `;
        }

        // Create booking number HTML if it exists
        let bookingNumberHtml = cottage.bookingNumber ? 
            `<p class="booking-number">Booking Number: ${cottage.bookingNumber}</p>` : '';
        
        cottageElement.innerHTML = `
            <h3>${cottage.cottageName || 'Unnamed Cottage'}</h3>
            <img src="${placeholderImage}" alt="${cottage.cottageName || 'Cottage'}" style="max-width: 100%; height: auto;">
            ${bookingNumberHtml}
            <p>Address: ${cottage.address || 'N/A'}</p>
            <p>Capacity: ${cottage.actualPlaces || 'N/A'} people, ${cottage.actualBedrooms || 'N/A'} bedrooms</p>
            <p>Distance to Lake: ${cottage.distanceToLake || 'N/A'} m</p>
            <p>Nearest City: ${cottage.nearestCity || 'N/A'} (${cottage.distanceToCity || 'N/A'} km)</p>
            <p>Available: ${cottage.isAvailable ? 'Yes' : 'No'}</p>
            ${bookingPeriodHtml}
        `;
        
        return cottageElement;
    }
});
