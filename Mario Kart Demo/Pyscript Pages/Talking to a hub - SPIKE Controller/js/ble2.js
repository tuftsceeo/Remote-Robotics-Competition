const SERVICE_UUID = '0000fd02-0000-1000-8000-00805f9b34fb';
const WRITE_UUID   = '0000fd02-0001-1000-8000-00805f9b34fb';
const NOTIFY_UUID  = '0000fd02-0002-1000-8000-00805f9b34fb';

export class BLEDevice {
    constructor() {
        this.device = null;
        this.server = null;
        this.service = null;
        this.writeCharacteristic = null;
        this.notifyCharacteristic = null;
        this.callback = null;

    }

    async scan(){
        this.device = await navigator.bluetooth.requestDevice({
                filters: [{ services: [SERVICE_UUID] }]});
    }

    async connect(mycallback) {
        this.callback = mycallback;
        if (this.device) {
            try {
                this.server = await this.device.gatt.connect();
                this.service = await this.server.getPrimaryService(SERVICE_UUID);
                this.writeCharacteristic = await this.service.getCharacteristic(WRITE_UUID);
                this.notifyCharacteristic = await this.service.getCharacteristic(NOTIFY_UUID);
                this.handleNotification = this.handleNotification.bind(this);
                await this.notifyCharacteristic.startNotifications();
                this.notifyCharacteristic.addEventListener('characteristicvaluechanged',
                    this.handleNotification);
            } catch (error) {
                console.error('Error connecting:', error);
            }
        }
    }

    handleNotification(event) {
        const value = event.target.value;
        const data = new Uint8Array(value.buffer);
        //console.log('got data')
        if (this.callback) {this.callback(NOTIFY_UUID, data)};
    }

    async send(data) {
        if (!this.writeCharacteristic) {
            console.error('Not connected to device');
            return;
        }
        try {
            const bytes = new Uint8Array(data);
            await this.writeCharacteristic.writeValue(bytes);
            console.log('Sent:', bytes);
        } catch (error) {
            console.error('Error writing:', error);
        }
    }

    disconnect() {
        if (this.device && this.device.gatt.connected) {
            this.device.gatt.disconnect();
        }
    }
}
