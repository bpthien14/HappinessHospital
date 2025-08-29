/**
 * Example: How to use Services Configuration
 * Cách sử dụng Services Configuration trong appointments.js
 */

// VÍ DỤ SỬ DỤNG SERVICES CONFIGURATION

// 1. Cách cũ (hardcode URL):
// const response = await axios.get('/api/appointments/');
// const doctorResponse = await axios.get('/api/doctors/');

// 2. Cách mới (sử dụng Services Configuration):

// === Cách 1: Sử dụng ServiceHelper (Đơn giản nhất) ===
async function loadAppointments_NEW() {
    try {
        // Thay vì: '/api/appointments/'
        const appointmentsURL = ServiceHelper.getAppointmentsURL();
        const response = await axios.get(appointmentsURL);
        
        // Thay vì: '/api/doctors/' 
        const doctorsURL = ServiceHelper.getDoctorsURL();
        const doctorResponse = await axios.get(doctorsURL);
        
        console.log('✅ URLs:', { appointmentsURL, doctorsURL });
        
    } catch (error) {
        console.error('❌ Error:', error);
    }
}

// === Cách 2: Sử dụng getEndpointURL (Linh hoạt hơn) ===
async function getAppointmentDetail_NEW(appointmentId) {
    try {
        // Tự động thay thế {id} bằng appointmentId
        const url = getEndpointURL('MAIN_APP', 'APPOINTMENTS') + `${appointmentId}/`;
        // Hoặc dùng ServiceHelper
        const url2 = ServiceHelper.getAppointmentDetailURL(appointmentId);
        
        const response = await axios.get(url);
        console.log('✅ Appointment detail URL:', url);
        
    } catch (error) {
        console.error('❌ Error:', error);
    }
}

// === Cách 3: Sử dụng getServiceURL (Khi cần custom endpoint) ===
async function customEndpoint_NEW() {
    try {
        const baseURL = getServiceURL('APPOINTMENTS_SERVICE'); // http://localhost:8003
        const customURL = `${baseURL}/api/appointments/statistics/`;
        
        const response = await axios.get(customURL);
        console.log('✅ Custom URL:', customURL);
        
    } catch (error) {
        console.error('❌ Error:', error);
    }
}

// === Cách 4: Chuyển đổi giữa Monolith và Microservices ===
function switchToMicroservices() {
    // Trong file services.js, đổi CURRENT_ENV = 'PRODUCTION'
    // Hoặc đổi USE_MICROSERVICES = true
    
    // Tất cả URL sẽ tự động chuyển từ:
    // http://localhost:8000/api/appointments/ (Monolith)
    // Sang:
    // http://localhost:8003/api/appointments/ (Microservice)
}

// === VÍ DỤ THỰC TẾ: Cập nhật loadAppointments function ===
async function loadAppointments_UPDATED(page = 1) {
    console.log('📅 Loading appointments, page:', page);
    
    try {
        // Build URL với params
        const params = new URLSearchParams({
            page: page,
            page_size: 10
        });

        // Thay vì hardcode '/api/appointments/'
        const baseURL = ServiceHelper.getAppointmentsURL();
        const url = `${baseURL}?${params.toString()}`;
        
        console.log('📅 API URL:', url);
        const response = await axios.get(url);
        
        // ... rest of the function
        
    } catch (error) {
        console.error('❌ Error loading appointments:', error);
    }
}

// === VÍ DỤ: Load form data với Services Config ===
async function loadFormData_UPDATED() {
    try {
        // Load patients
        const patientsURL = ServiceHelper.getPatientsURL();
        const patientResponse = await axios.get(patientsURL);
        
        // Load doctors
        const doctorsURL = ServiceHelper.getDoctorsURL();
        const doctorResponse = await axios.get(doctorsURL);
        
        // Load departments
        const departmentsURL = ServiceHelper.getDepartmentsURL();
        const departmentResponse = await axios.get(departmentsURL);
        
        console.log('✅ Form data URLs:', {
            patients: patientsURL,
            doctors: doctorsURL,
            departments: departmentsURL
        });
        
    } catch (error) {
        console.error('❌ Error loading form data:', error);
    }
}

// === VÍ DỤ: CRUD Operations với Services Config ===
async function createAppointment_UPDATED(formData) {
    try {
        const url = ServiceHelper.getAppointmentsURL();
        const response = await axios.post(url, formData);
        console.log('✅ Created appointment via:', url);
        return response.data;
    } catch (error) {
        console.error('❌ Error creating appointment:', error);
        throw error;
    }
}

async function updateAppointment_UPDATED(appointmentId, formData) {
    try {
        const url = ServiceHelper.getAppointmentDetailURL(appointmentId);
        const response = await axios.put(url, formData);
        console.log('✅ Updated appointment via:', url);
        return response.data;
    } catch (error) {
        console.error('❌ Error updating appointment:', error);
        throw error;
    }
}

async function deleteAppointment_UPDATED(appointmentId) {
    try {
        const url = ServiceHelper.getAppointmentDetailURL(appointmentId);
        await axios.delete(url);
        console.log('✅ Deleted appointment via:', url);
    } catch (error) {
        console.error('❌ Error deleting appointment:', error);
        throw error;
    }
}

// === LỢI ÍCH CUA SERVICES CONFIGURATION ===

/*
1. 🎯 CENTRALIZED MANAGEMENT:
   - Tất cả URL được quản lý ở một nơi
   - Dễ dàng thay đổi port/host của service
   - Không cần tìm kiếm trong nhiều file

2. 🔄 EASY MIGRATION:
   - Chuyển từ Monolith sang Microservices chỉ bằng cách đổi config
   - Không cần sửa code trong từng file

3. 🛠 ENVIRONMENT SPECIFIC:
   - Development: dùng localhost:8000 (monolith)
   - Production: dùng microservices trên các port khác nhau

4. 🐛 DEBUGGING:
   - Dễ dàng debug URL nào đang được gọi
   - Console.log các URL để kiểm tra

5. 🧪 TESTING:
   - Dễ dàng switch service endpoints cho testing
   - Mock services bằng cách đổi URL

VÍ DỤ THAY ĐỔI PORT:
- Muốn đổi Prescriptions Service từ port 8004 sang 9004?
- Chỉ cần sửa trong services.js:
  PRESCRIPTIONS_SERVICE: {
    PORT: 9004,  // Thay vì 8004
    BASE_URL: 'http://localhost:9004'
  }
- Tất cả API calls sẽ tự động dùng port mới!
*/

console.log('📖 Services Configuration Examples Loaded');
