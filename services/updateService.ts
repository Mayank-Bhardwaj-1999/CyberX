import * as Updates from 'expo-updates';
import { Alert } from 'react-native';

export class UpdateService {
  private static checking = false;

  /**
   * Check for updates and prompt user
   */
  static async checkForUpdates(silent: boolean = false): Promise<void> {
    // Skip in development mode
    if (__DEV__) {
      console.log('🔄 Updates disabled in development mode');
      return;
    }

    // Prevent multiple simultaneous checks
    if (this.checking) {
      console.log('🔄 Update check already in progress');
      return;
    }

    this.checking = true;

    try {
      console.log('🔍 Checking for updates...');
      
      const update = await Updates.checkForUpdateAsync();
      
      if (update.isAvailable) {
        console.log('✅ Update available!', update);
        
        if (!silent) {
          this.showUpdateAlert();
        } else {
          // Auto-install silent updates
          await this.downloadAndInstallUpdate();
        }
      } else {
        console.log('✅ App is up to date');
        if (!silent) {
          Alert.alert(
            'Up to Date',
            'Your app is already running the latest version!',
            [{ text: 'OK' }]
          );
        }
      }
    } catch (error) {
      console.error('❌ Error checking for updates:', error);
      if (!silent) {
        Alert.alert(
          'Update Check Failed',
          'Unable to check for updates. Please try again later.',
          [{ text: 'OK' }]
        );
      }
    } finally {
      this.checking = false;
    }
  }

  /**
   * Show update confirmation dialog
   */
  private static showUpdateAlert(): void {
    Alert.alert(
      'Update Available! 🚀',
      'A new version of CyberX is ready to install with the latest cybersecurity features and bug fixes.',
      [
        {
          text: 'Later',
          style: 'cancel',
          onPress: () => console.log('📅 Update postponed')
        },
        {
          text: 'Update Now',
          onPress: () => this.downloadAndInstallUpdate(),
          style: 'default'
        }
      ],
      { cancelable: false }
    );
  }

  /**
   * Download and install update
   */
  private static async downloadAndInstallUpdate(): Promise<void> {
    try {
      console.log('⬇️ Downloading update...');
      
      // Show downloading progress
      Alert.alert(
        'Downloading Update',
        'Please wait while the update is being downloaded...',
        [],
        { cancelable: false }
      );

      await Updates.fetchUpdateAsync();
      
      console.log('✅ Update downloaded successfully');
      
      // Show installation confirmation
      Alert.alert(
        'Update Ready! ✨',
        'The update has been downloaded. Restart the app to apply changes.',
        [
          {
            text: 'Restart Now',
            onPress: () => {
              console.log('🔄 Restarting app with updates...');
              Updates.reloadAsync();
            },
            style: 'default'
          }
        ],
        { cancelable: false }
      );
      
    } catch (error) {
      console.error('❌ Error downloading update:', error);
      Alert.alert(
        'Update Failed',
        'Failed to download the update. Please check your internet connection and try again.',
        [{ text: 'OK' }]
      );
    }
  }

  /**
   * Force check for critical updates on app launch
   */
  static async checkForCriticalUpdates(): Promise<void> {
    // Only check on app launch in production
    if (__DEV__) return;

    try {
      console.log('🔍 Checking for critical updates on startup...');
      
      const update = await Updates.checkForUpdateAsync();
      
      if (update.isAvailable) {
        // Critical updates are auto-installed
        console.log('🚨 Critical update found, auto-installing...');
        await Updates.fetchUpdateAsync();
        
        Alert.alert(
          'Critical Update Applied',
          'A critical security update has been installed. The app will restart now.',
          [
            {
              text: 'Restart',
              onPress: () => Updates.reloadAsync()
            }
          ],
          { cancelable: false }
        );
      }
    } catch (error) {
      console.error('❌ Error checking critical updates:', error);
      // Fail silently for critical update checks
    }
  }

  /**
   * Get current app version and update info
   */
  static async getAppInfo(): Promise<{
    currentVersion: string;
    updateId: string | null;
    isEmbeddedLaunch: boolean;
  }> {
    const currentVersion = '1.0.0'; // Use your app.json version
    const updateId = Updates.updateId || null;
    const isEmbeddedLaunch = Updates.isEmbeddedLaunch;

    return {
      currentVersion,
      updateId,
      isEmbeddedLaunch
    };
  }
}
