/**
 * JavaScript para la aplicación Students
 * Sistema integral de gestión de alumnos
 * 
 * Características implementadas:
 * - Validación en tiempo real
 * - Búsqueda y filtrado dinámico  
 * - Selección múltiple y acciones masivas
 * - AJAX para operaciones asíncronas
 * - UX mejorada con animaciones
 */

class StudentsApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.setupValidation();
        this.setupSearch();
        this.setupBulkActions();
    }

    setupEventListeners() {
        // Event listeners principales
        document.addEventListener('DOMContentLoaded', () => {
            console.log('Students App initialized');
        });

        // Cerrar alertas automáticamente
        this.autoCloseAlerts();
        
        // Tooltips de Bootstrap
        this.initTooltips();
    }

    initializeComponents() {
        // Inicializar componentes de Bootstrap
        if (typeof bootstrap !== 'undefined') {
            // Tooltips
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });

            // Popovers
            const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        }
    }

    /**
     * Configurar validación en tiempo real para formularios
     */
    setupValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        
        forms.forEach(form => {
            // Validación en tiempo real
            const inputs = form.querySelectorAll('input, select, textarea');
            
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });

                input.addEventListener('input', () => {
                    if (input.classList.contains('is-invalid') || input.classList.contains('is-valid')) {
                        this.validateField(input);
                    }
                });
            });

            // Prevenir envío si hay errores
            form.addEventListener('submit', (event) => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    this.showFormErrors(form);
                }
                form.classList.add('was-validated');
            });
        });
    }

    /**
     * Validar un campo individual
     */
    validateField(field) {
        const isValid = field.checkValidity();
        
        field.classList.remove('is-valid', 'is-invalid');
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');

        // Limpiar mensajes previos
        const existingFeedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }

        // Agregar mensaje de validación
        const feedback = document.createElement('div');
        feedback.className = isValid ? 'valid-feedback' : 'invalid-feedback';
        feedback.textContent = isValid ? '¡Correcto!' : field.validationMessage;
        
        field.parentNode.appendChild(feedback);

        return isValid;
    }

    /**
     * Mostrar errores del formulario
     */
    showFormErrors(form) {
        const invalidFields = form.querySelectorAll(':invalid');
        if (invalidFields.length > 0) {
            invalidFields[0].focus();
            
            this.showNotification(
                'error',
                'Por favor, corrija los errores en el formulario',
                'Hay campos con información incorrecta o incompleta'
            );
        }
    }

    /**
     * Configurar búsqueda en tiempo real
     */
    setupSearch() {
        const searchInputs = document.querySelectorAll('[data-search-target]');
        
        searchInputs.forEach(input => {
            let timeout;
            
            input.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.performSearch(input);
                }, 300); // Debounce de 300ms
            });
        });
    }

    /**
     * Realizar búsqueda
     */
    performSearch(input) {
        const target = input.getAttribute('data-search-target');
        const searchTerm = input.value.toLowerCase().trim();
        const targetElement = document.querySelector(target);

        if (!targetElement) return;

        const searchableElements = targetElement.querySelectorAll('[data-searchable]');
        let visibleCount = 0;

        searchableElements.forEach(element => {
            const searchText = element.textContent.toLowerCase();
            const isVisible = searchText.includes(searchTerm) || searchTerm === '';
            
            element.style.display = isVisible ? '' : 'none';
            if (isVisible) visibleCount++;
        });

        // Mostrar mensaje si no hay resultados
        this.updateSearchResults(targetElement, visibleCount, searchTerm);
    }

    /**
     * Actualizar resultados de búsqueda
     */
    updateSearchResults(container, count, searchTerm) {
        const existingMessage = container.querySelector('.search-no-results');
        
        if (count === 0 && searchTerm) {
            if (!existingMessage) {
                const message = document.createElement('div');
                message.className = 'search-no-results text-center py-4';
                message.innerHTML = `
                    <div class="text-muted">
                        <i class="fas fa-search fa-2x mb-2"></i>
                        <p>No se encontraron resultados para "<strong>${searchTerm}</strong>"</p>
                    </div>
                `;
                container.appendChild(message);
            }
        } else if (existingMessage) {
            existingMessage.remove();
        }
    }

    /**
     * Configurar acciones masivas
     */
    setupBulkActions() {
        const selectAllCheckbox = document.querySelector('#select-all');
        const rowCheckboxes = document.querySelectorAll('.row-select');
        const bulkActionButtons = document.querySelectorAll('[data-bulk-action]');

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', () => {
                rowCheckboxes.forEach(checkbox => {
                    checkbox.checked = selectAllCheckbox.checked;
                });
                this.updateBulkActionButtons();
            });
        }

        rowCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkActionButtons();
                
                // Actualizar estado del select-all
                if (selectAllCheckbox) {
                    const checkedCount = document.querySelectorAll('.row-select:checked').length;
                    selectAllCheckbox.checked = checkedCount === rowCheckboxes.length;
                    selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < rowCheckboxes.length;
                }
            });
        });

        // Configurar botones de acción masiva
        bulkActionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const action = button.getAttribute('data-bulk-action');
                this.performBulkAction(action);
            });
        });
    }

    /**
     * Actualizar estado de botones de acción masiva
     */
    updateBulkActionButtons() {
        const selectedCount = document.querySelectorAll('.row-select:checked').length;
        const bulkActionContainer = document.querySelector('#bulk-actions');
        const bulkActionButtons = document.querySelectorAll('[data-bulk-action]');

        if (bulkActionContainer) {
            bulkActionContainer.disabled = selectedCount === 0;
        }

        bulkActionButtons.forEach(button => {
            button.disabled = selectedCount === 0;
            
            // Actualizar texto con contador
            const originalText = button.getAttribute('data-original-text') || button.textContent;
            if (!button.getAttribute('data-original-text')) {
                button.setAttribute('data-original-text', originalText);
            }
            
            if (selectedCount > 0) {
                button.textContent = `${originalText} (${selectedCount})`;
            } else {
                button.textContent = originalText;
            }
        });
    }

    /**
     * Realizar acción masiva
     */
    performBulkAction(action) {
        const selectedIds = Array.from(document.querySelectorAll('.row-select:checked'))
            .map(checkbox => checkbox.value);

        if (selectedIds.length === 0) {
            this.showNotification('warning', 'Seleccione al menos un elemento');
            return;
        }

        // Configuración de acciones
        const actions = {
            activate: {
                title: 'Activar Alumnos',
                message: `¿Activar ${selectedIds.length} alumno(s) seleccionado(s)?`,
                url: '/students/acciones/activar/',
                class: 'btn-success'
            },
            deactivate: {
                title: 'Desactivar Alumnos',
                message: `¿Desactivar ${selectedIds.length} alumno(s) seleccionado(s)?`,
                url: '/students/acciones/desactivar/',
                class: 'btn-warning'
            },
            delete: {
                title: 'Eliminar Alumnos',
                message: `¿ELIMINAR ${selectedIds.length} alumno(s) seleccionado(s)?\n\nEsta acción no se puede deshacer.`,
                url: '/students/acciones/eliminar/',
                class: 'btn-danger',
                dangerous: true
            }
        };

        const actionConfig = actions[action];
        if (!actionConfig) return;

        this.showConfirmation(
            actionConfig.title,
            actionConfig.message,
            () => this.executeBulkAction(actionConfig.url, selectedIds),
            actionConfig.dangerous
        );
    }

    /**
     * Ejecutar acción masiva
     */
    executeBulkAction(url, selectedIds) {
        this.showLoading('Procesando...');

        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());
        selectedIds.forEach(id => formData.append('selected_ids', id));

        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            this.hideLoading();
            
            if (data.success) {
                this.showNotification('success', data.message);
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.showNotification('error', data.message || 'Error al procesar la acción');
            }
        })
        .catch(error => {
            this.hideLoading();
            console.error('Error:', error);
            this.showNotification('error', 'Error de conexión. Intente nuevamente.');
        });
    }

    /**
     * Mostrar notificación
     */
    showNotification(type, message, title = '') {
        // Crear el HTML de la notificación
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const icon = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-triangle',
            'warning': 'fas fa-exclamation-circle',
            'info': 'fas fa-info-circle'
        }[type] || 'fas fa-info-circle';

        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${icon} me-2 fs-5"></i>
                <div>
                    ${title ? `<strong>${title}</strong><br>` : ''}
                    ${message}
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Mostrar confirmación
     */
    showConfirmation(title, message, onConfirm, dangerous = false) {
        const modalId = 'confirmationModal';
        let modal = document.getElementById(modalId);

        if (!modal) {
            modal = this.createConfirmationModal(modalId);
            document.body.appendChild(modal);
        }

        // Actualizar contenido
        modal.querySelector('.modal-title').textContent = title;
        modal.querySelector('.modal-body p').textContent = message;
        
        const confirmBtn = modal.querySelector('.btn-confirm');
        confirmBtn.className = `btn ${dangerous ? 'btn-danger' : 'btn-primary'}`;
        confirmBtn.textContent = dangerous ? 'Eliminar' : 'Confirmar';

        // Event listener para confirmación
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        newConfirmBtn.addEventListener('click', () => {
            bootstrap.Modal.getInstance(modal).hide();
            onConfirm();
        });

        // Mostrar modal
        new bootstrap.Modal(modal).show();
    }

    /**
     * Crear modal de confirmación
     */
    createConfirmationModal(modalId) {
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirmar Acción</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>¿Está seguro de realizar esta acción?</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary btn-confirm">Confirmar</button>
                    </div>
                </div>
            </div>
        `;
        return modal;
    }

    /**
     * Mostrar loading
     */
    showLoading(message = 'Cargando...') {
        const loadingId = 'globalLoading';
        let loading = document.getElementById(loadingId);

        if (!loading) {
            loading = document.createElement('div');
            loading.id = loadingId;
            loading.className = 'loading-overlay';
            loading.innerHTML = `
                <div class="text-center">
                    <div class="custom-spinner mb-3"></div>
                    <p class="mb-0">${message}</p>
                </div>
            `;
            document.body.appendChild(loading);
        } else {
            loading.querySelector('p').textContent = message;
            loading.style.display = 'flex';
        }
    }

    /**
     * Ocultar loading
     */
    hideLoading() {
        const loading = document.getElementById('globalLoading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    /**
     * Auto-cerrar alertas
     */
    autoCloseAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            setTimeout(() => {
                if (alert.parentNode) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        });
    }

    /**
     * Inicializar tooltips
     */
    initTooltips() {
        if (typeof bootstrap !== 'undefined') {
            const tooltips = document.querySelectorAll('[title], [data-bs-title]');
            tooltips.forEach(element => {
                if (!element.hasAttribute('data-bs-toggle')) {
                    element.setAttribute('data-bs-toggle', 'tooltip');
                    new bootstrap.Tooltip(element);
                }
            });
        }
    }

    /**
     * Obtener CSRF token
     */
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    /**
     * Utilidades de formato
     */
    formatNumber(number) {
        return new Intl.NumberFormat('es-AR').format(number);
    }

    formatDate(date, options = {}) {
        const defaultOptions = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        return new Intl.DateTimeFormat('es-AR', {...defaultOptions, ...options}).format(new Date(date));
    }

    /**
     * Validaciones personalizadas
     */
    validateDNI(dni) {
        const cleaned = dni.replace(/\D/g, '');
        return cleaned.length >= 7 && cleaned.length <= 8 && !cleaned.startsWith('0');
    }

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.studentsApp = new StudentsApp();
});

// Exportar para uso en otros scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StudentsApp;
}
