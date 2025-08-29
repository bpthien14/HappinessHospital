/**
 * Hospital Microservices Configuration
 * Centralized service endpoints management
 */

// Service Configuration
const SERVICES = {
    // API Gateway & Load Balancer
    NGINX: {
        HOST: 'localhost',
        HTTP_PORT: 80,
        HTTPS_PORT: 443,
        BASE_URL: 'http://localhost'
    },

    // Message Queue
    RABBITMQ: {
        HOST: 'localhost',
        AMQP_PORT: 5672,
        MANAGEMENT_PORT: 15672,
        MANAGEMENT_URL: 'http://localhost:15672'
    },

    // Core Microservices
    AUTH_SERVICE: {
        HOST: 'localhost',
        PORT: 8001,
        BASE_URL: 'http://localhost:8001',
        ENDPOINTS: {
            LOGIN: '/api/auth/login/',
            LOGOUT: '/api/auth/logout/',
            REFRESH: '/api/auth/refresh/',
            REGISTER: '/api/auth/register/',
            PROFILE: '/api/auth/profile/',
            CHANGE_PASSWORD: '/api/auth/change-password/'
        }
    },

    PATIENTS_SERVICE: {
        HOST: 'localhost',
        PORT: 8002,
        BASE_URL: 'http://localhost:8002',
        ENDPOINTS: {
            LIST: '/api/patients/',
            DETAIL: '/api/patients/{id}/',
            STATISTICS: '/api/patients/statistics/',
            VALIDATE_INSURANCE: '/api/patients/validate-insurance/',
            GEO_PROVINCES: '/api/geo/provinces/',
            MEDICAL_RECORDS: '/api/patients/{id}/medical-records/'
        }
    },

    APPOINTMENTS_SERVICE: {
        HOST: 'localhost',
        PORT: 8003,
        BASE_URL: 'http://localhost:8003',
        ENDPOINTS: {
            LIST: '/api/appointments/',
            DETAIL: '/api/appointments/{id}/',
            CONFIRM: '/api/appointments/{id}/confirm/',
            CHECKIN: '/api/appointments/{id}/checkin/',
            CANCEL: '/api/appointments/{id}/cancel/',
            AVAILABLE_SLOTS: '/api/appointments/available-slots/',
            STATISTICS: '/api/appointments/statistics/',
            DEPARTMENTS: '/api/departments/',
            DOCTORS: '/api/doctors/'
        }
    },

    PRESCRIPTIONS_SERVICE: {
        HOST: 'localhost',
        PORT: 8004,
        BASE_URL: 'http://localhost:8004',
        ENDPOINTS: {
            LIST: '/api/prescriptions/',
            DETAIL: '/api/prescriptions/{id}/',
            DRUGS: '/api/drugs/',
            DRUG_CATEGORIES: '/api/drug-categories/',
            DISPENSE: '/api/prescriptions/{id}/dispense/',
            REFILL: '/api/prescriptions/{id}/refill/'
        }
    },

    PAYMENTS_SERVICE: {
        HOST: 'localhost',
        PORT: 8005,
        BASE_URL: 'http://localhost:8005',
        ENDPOINTS: {
            LIST: '/api/payments/',
            DETAIL: '/api/payments/{id}/',
            CREATE_VNPAY: '/api/payments/vnpay/create/',
            VNPAY_RETURN: '/api/payments/vnpay/return/',
            VNPAY_IPN: '/api/payments/vnpay/ipn/',
            QR_CODE: '/api/payments/{id}/qr-code/'
        }
    },

    NOTIFICATIONS_SERVICE: {
        HOST: 'localhost',
        PORT: 8006,
        BASE_URL: 'http://localhost:8006',
        ENDPOINTS: {
            LIST: '/api/notifications/',
            MARK_READ: '/api/notifications/{id}/mark-read/',
            MARK_ALL_READ: '/api/notifications/mark-all-read/',
            SEND: '/api/notifications/send/'
        }
    },

    // Current Monolith App (fallback)
    MAIN_APP: {
        HOST: 'localhost',
        PORT: 8000,
        BASE_URL: 'http://localhost:8000',
        ENDPOINTS: {
            // Auth
            LOGIN: '/api/auth/login/',
            LOGOUT: '/api/auth/logout/',
            REFRESH: '/api/auth/refresh/',
            
            // Users
            USERS: '/api/users/',
            
            // Patients
            PATIENTS: '/api/patients/',
            PATIENTS_STATISTICS: '/api/patients/statistics/',
            GEO_PROVINCES: '/api/geo/provinces/',
            
            // Appointments
            APPOINTMENTS: '/api/appointments/',
            DEPARTMENTS: '/api/departments/',
            DOCTORS: '/api/doctors/',
            
            // Prescriptions
            PRESCRIPTIONS: '/api/prescriptions/',
            DRUGS: '/api/drugs/',
            
            // Payments
            PAYMENTS: '/api/payments/'
        }
    }
};

// Environment Configuration
const ENV_CONFIG = {
    DEVELOPMENT: {
        USE_MICROSERVICES: false, // Set to true when using microservices
        DEFAULT_SERVICE: 'MAIN_APP'
    },
    PRODUCTION: {
        USE_MICROSERVICES: true,
        DEFAULT_SERVICE: 'NGINX'
    }
};

// Current Environment
const CURRENT_ENV = 'DEVELOPMENT'; // Change to 'PRODUCTION' when deploying

/**
 * Get service URL by service name
 * @param {string} serviceName - Name of the service (e.g., 'PATIENTS_SERVICE')
 * @returns {string} Base URL of the service
 */
function getServiceURL(serviceName) {
    const service = SERVICES[serviceName];
    if (!service) {
        console.error(`Service ${serviceName} not found!`);
        return SERVICES.MAIN_APP.BASE_URL;
    }
    return service.BASE_URL;
}

/**
 * Get full endpoint URL
 * @param {string} serviceName - Name of the service
 * @param {string} endpointName - Name of the endpoint
 * @param {object} params - Parameters to replace in URL (e.g., {id: 123})
 * @returns {string} Full endpoint URL
 */
function getEndpointURL(serviceName, endpointName, params = {}) {
    const service = SERVICES[serviceName];
    if (!service || !service.ENDPOINTS) {
        console.error(`Service ${serviceName} or endpoints not found!`);
        return '';
    }

    const endpoint = service.ENDPOINTS[endpointName];
    if (!endpoint) {
        console.error(`Endpoint ${endpointName} not found in ${serviceName}!`);
        return '';
    }

    let url = service.BASE_URL + endpoint;
    
    // Replace parameters in URL
    Object.keys(params).forEach(key => {
        url = url.replace(`{${key}}`, params[key]);
    });

    return url;
}

/**
 * Get current service configuration based on environment
 * @returns {object} Current service configuration
 */
function getCurrentServiceConfig() {
    const envConfig = ENV_CONFIG[CURRENT_ENV];
    
    if (envConfig.USE_MICROSERVICES) {
        return {
            AUTH: SERVICES.AUTH_SERVICE,
            PATIENTS: SERVICES.PATIENTS_SERVICE,
            APPOINTMENTS: SERVICES.APPOINTMENTS_SERVICE,
            PRESCRIPTIONS: SERVICES.PRESCRIPTIONS_SERVICE,
            PAYMENTS: SERVICES.PAYMENTS_SERVICE,
            NOTIFICATIONS: SERVICES.NOTIFICATIONS_SERVICE
        };
    } else {
        // Use main app for all services
        return {
            AUTH: SERVICES.MAIN_APP,
            PATIENTS: SERVICES.MAIN_APP,
            APPOINTMENTS: SERVICES.MAIN_APP,
            PRESCRIPTIONS: SERVICES.MAIN_APP,
            PAYMENTS: SERVICES.MAIN_APP,
            NOTIFICATIONS: SERVICES.MAIN_APP
        };
    }
}

// Export for use in other files
window.SERVICES = SERVICES;
window.getServiceURL = getServiceURL;
window.getEndpointURL = getEndpointURL;
window.getCurrentServiceConfig = getCurrentServiceConfig;

// Helper functions for common operations
window.ServiceHelper = {
    // Auth service helpers
    getAuthLoginURL: () => getEndpointURL('MAIN_APP', 'LOGIN'),
    getAuthLogoutURL: () => getEndpointURL('MAIN_APP', 'LOGOUT'),
    getAuthRefreshURL: () => getEndpointURL('MAIN_APP', 'REFRESH'),
    
    // Patients service helpers
    getPatientsURL: () => getEndpointURL('MAIN_APP', 'PATIENTS'),
    getPatientDetailURL: (id) => getEndpointURL('MAIN_APP', 'PATIENTS') + `${id}/`,
    getPatientsStatsURL: () => getEndpointURL('MAIN_APP', 'PATIENTS_STATISTICS'),
    
    // Appointments service helpers
    getAppointmentsURL: () => getEndpointURL('MAIN_APP', 'APPOINTMENTS'),
    getAppointmentDetailURL: (id) => getEndpointURL('MAIN_APP', 'APPOINTMENTS') + `${id}/`,
    getDepartmentsURL: () => getEndpointURL('MAIN_APP', 'DEPARTMENTS'),
    getDoctorsURL: () => getEndpointURL('MAIN_APP', 'DOCTORS'),
    
    // Prescriptions service helpers
    getPrescriptionsURL: () => getEndpointURL('MAIN_APP', 'PRESCRIPTIONS'),
    getPrescriptionDetailURL: (id) => getEndpointURL('MAIN_APP', 'PRESCRIPTIONS') + `${id}/`,
    getDrugsURL: () => getEndpointURL('MAIN_APP', 'DRUGS'),
    
    // Payments service helpers
    getPaymentsURL: () => getEndpointURL('MAIN_APP', 'PAYMENTS'),
    getPaymentDetailURL: (id) => getEndpointURL('MAIN_APP', 'PAYMENTS') + `${id}/`,
    
    // Generic helper
    getURL: (serviceName, endpoint, params = {}) => {
        return getEndpointURL(serviceName, endpoint, params);
    }
};

console.log('🏥 Hospital Services Configuration Loaded');
console.log('📍 Current Environment:', CURRENT_ENV);
console.log('🔧 Service Config:', getCurrentServiceConfig());
