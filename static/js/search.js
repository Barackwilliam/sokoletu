class AdvancedSearch {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.suggestionsContainer = document.getElementById('searchSuggestions');
        this.debounceTimeout = null;
        
        this.init();
    }
    
    init() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.handleInput.bind(this));
            this.searchInput.addEventListener('focus', this.showSuggestions.bind(this));
            document.addEventListener('click', this.hideSuggestions.bind(this));
        }
        
        // Initialize price range filters
        this.initPriceFilters();
    }
    
    handleInput(event) {
        const query = event.target.value.trim();
        
        clearTimeout(this.debounceTimeout);
        
        if (query.length < 2) {
            this.hideSuggestions();
            return;
        }
        
        this.debounceTimeout = setTimeout(() => {
            this.fetchSuggestions(query);
        }, 300);
    }
    
    async fetchSuggestions(query) {
        try {
            const response = await fetch(`/market/search/suggestions/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.displaySuggestions(data.suggestions);
        } catch (error) {
            console.error('Search error:', error);
        }
    }
    
    displaySuggestions(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        const html = suggestions.map(suggestion => `
            <a href="${suggestion.url}" class="list-group-item list-group-item-action border-0 py-3">
                <div class="d-flex align-items-center">
                    ${suggestion.type === 'product' ? `
                        <div class="bg-light rounded p-2 me-3">
                            <i class="fas fa-box text-warning"></i>
                        </div>
                    ` : `
                        <div class="bg-light rounded p-2 me-3">
                            <i class="fas fa-folder text-warning"></i>
                        </div>
                    `}
                    <div class="flex-grow-1">
                        <h6 class="mb-1 text-dark">${suggestion.name}</h6>
                        <small class="text-muted">${suggestion.category || 'Category'}</small>
                    </div>
                    <i class="fas fa-chevron-right text-muted"></i>
                </div>
            </a>
        `).join('');
        
        this.suggestionsContainer.innerHTML = html;
        this.showSuggestions();
    }
    
    showSuggestions() {
        if (this.suggestionsContainer.children.length > 0) {
            this.suggestionsContainer.style.display = 'block';
        }
    }
    
    hideSuggestions(event) {
        if (event && (this.suggestionsContainer.contains(event.target) || 
                      this.searchInput.contains(event.target))) {
            return;
        }
        
        this.suggestionsContainer.style.display = 'none';
    }
    
    initPriceFilters() {
        const minPrice = document.querySelector('input[name="min_price"]');
        const maxPrice = document.querySelector('input[name="max_price"]');
        
        if (minPrice && maxPrice) {
            [minPrice, maxPrice].forEach(input => {
                input.addEventListener('change', this.debounce(() => {
                    document.getElementById('filter-form').submit();
                }, 1000));
            });
        }
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new AdvancedSearch();
});