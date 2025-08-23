import NetInfo from '@react-native-community/netinfo';

export interface NetworkStatus {
  isConnected: boolean;
  connectionType: string | null;
  isInternetReachable: boolean | null;
}

export const getNetworkStatus = async (): Promise<NetworkStatus> => {
  try {
    const netInfo = await NetInfo.fetch();
    return {
      isConnected: netInfo.isConnected ?? false,
      connectionType: netInfo.type,
      isInternetReachable: netInfo.isInternetReachable,
    };
  } catch (error) {
    console.error('Error fetching network status:', error);
    return {
      isConnected: false,
      connectionType: null,
      isInternetReachable: false,
    };
  }
};

export const subscribeToNetworkStatus = (callback: (status: NetworkStatus) => void) => {
  const unsubscribe = NetInfo.addEventListener(state => {
    const status: NetworkStatus = {
      isConnected: state.isConnected ?? false,
      connectionType: state.type,
      isInternetReachable: state.isInternetReachable,
    };
    callback(status);
  });
  
  return unsubscribe;
};
