#!/usr/bin/env node

const fs = require('fs');
const os = require('os');
const path = require('path');

/**
 * Get the local IP address of the machine
 * @returns {string} The local IP address
 */
function getLocalIPAddress() {
  const interfaces = os.networkInterfaces();
  
  // Priority order: WiFi, Ethernet, other
  const priorityOrder = ['Wi-Fi', 'WiFi', 'Wireless', 'Ethernet', 'eth0', 'en0', 'wlan0'];
  
  for (const interfaceName of priorityOrder) {
    const networkInterface = interfaces[interfaceName];
    if (networkInterface) {
      for (const details of networkInterface) {
        if (details.family === 'IPv4' && !details.internal) {
          return details.address;
        }
      }
    }
  }
  
  // Fallback: find any non-internal IPv4 address
  for (const interfaceName in interfaces) {
    const networkInterface = interfaces[interfaceName];
    for (const details of networkInterface) {
      if (details.family === 'IPv4' && !details.internal) {
        return details.address;
      }
    }
  }
  
  // Last resort fallback
  return '127.0.0.1';
}

/**
 * Update the .env file with the current IP address
 */
function updateEnvFile() {
  const envPath = path.join(process.cwd(), '.env');
  const localIP = getLocalIPAddress();
  const apiUrl = `http://${localIP}:8080`;
  
  console.log('🔍 Detecting network configuration...');
  console.log(`📍 Local IP Address: ${localIP}`);
  console.log(`🌐 API URL: ${apiUrl}`);
  
  try {
    let envContent = '';
    
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
      console.log('📄 Found existing .env file');
    } else {
      console.log('📄 Creating new .env file');
    }
    
    // Update or add the EXPO_PUBLIC_API_URL
    const apiUrlPattern = /^EXPO_PUBLIC_API_URL=.*$/m;
    const newApiUrlLine = `EXPO_PUBLIC_API_URL=${apiUrl}`;
    
    if (apiUrlPattern.test(envContent)) {
      // Update existing line
      envContent = envContent.replace(apiUrlPattern, newApiUrlLine);
      console.log('✅ Updated existing API URL configuration');
    } else {
      // Add new line
      if (envContent && !envContent.endsWith('\n')) {
        envContent += '\n';
      }
      envContent += `\n# Auto-detected API Configuration\n${newApiUrlLine}\n`;
      console.log('✅ Added new API URL configuration');
    }
    
    // Ensure other required variables exist
    const requiredVars = {
      'APP_NAME': 'CyberX News',
      'APP_VERSION': '1.0.0'
    };
    
    for (const [varName, defaultValue] of Object.entries(requiredVars)) {
      const varPattern = new RegExp(`^${varName}=.*$`, 'm');
      if (!varPattern.test(envContent)) {
        envContent += `${varName}=${defaultValue}\n`;
        console.log(`✅ Added ${varName} configuration`);
      }
    }
    
    // Write the updated content
    fs.writeFileSync(envPath, envContent);
    console.log('💾 Saved .env file successfully');
    
    // Show network interfaces for reference
    console.log('\n📊 Available Network Interfaces:');
    const interfaces = os.networkInterfaces();
    for (const [name, details] of Object.entries(interfaces)) {
      const ipv4 = details.find(d => d.family === 'IPv4' && !d.internal);
      if (ipv4) {
        console.log(`  ${name}: ${ipv4.address}`);
      }
    }
    
    console.log('\n🎉 Environment configuration updated successfully!');
    console.log(`💡 Your React Native app will now connect to: ${apiUrl}`);
    console.log('🔄 Restart your Expo development server to apply changes');
    
  } catch (error) {
    console.error('❌ Error updating .env file:', error.message);
    process.exit(1);
  }
}

// Run the script
if (require.main === module) {
  updateEnvFile();
}

module.exports = { getLocalIPAddress, updateEnvFile };
