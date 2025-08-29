// Simple test to create prescription via browser console
// Run this in browser developer console

async function testPrescriptionAPI() {
    console.log('🧪 Testing prescription creation API...');
    
    // Get sample data from current page
    if (typeof patients === 'undefined' || !patients.length) {
        console.error('❌ No patients available');
        return;
    }
    
    if (typeof drugs === 'undefined' || !drugs.length) {
        console.error('❌ No drugs available');
        return;
    }
    
    const testData = {
        patient: patients[0].id,
        doctor: 1,
        prescription_type: 'OUTPATIENT',
        diagnosis: 'Test từ console',
        notes: 'Test notes từ console',
        special_instructions: 'Test special instructions',
        valid_from: new Date().toISOString(),
        valid_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        items: [
            {
                drug: drugs[0].id,
                quantity: 3,
                dosage_per_time: '1 viên',
                frequency: '3X_DAILY',
                route: 'ORAL',
                duration_days: 7,
                instructions: 'Uống sau ăn theo chỉ định'
            }
        ]
    };
    
    console.log('📤 Sending data:', JSON.stringify(testData, null, 2));
    
    try {
        const response = await axios.post('/api/prescriptions/', testData, {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('✅ Success:', response.data);
        alert('Tạo đơn thuốc thành công!');
        
    } catch (error) {
        console.error('❌ Error:', error);
        console.error('❌ Response data:', error.response?.data);
        alert('Lỗi: ' + JSON.stringify(error.response?.data || error.message));
    }
}

// Run the test
testPrescriptionAPI();
