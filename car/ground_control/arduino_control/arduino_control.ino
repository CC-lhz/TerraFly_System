// 引脚定义
#define MOTOR1_IN1 2
#define MOTOR1_IN2 3
#define MOTOR2_IN1 4
#define MOTOR2_IN2 5
#define MOTOR3_IN1 6
#define MOTOR3_IN2 7
#define MOTOR4_IN1 8
#define MOTOR4_IN2 9

#define MOTOR1_EN 10  // 电机1使能（PWM）
#define MOTOR2_EN 11  // 电机2使能（PWM）
#define MOTOR3_EN 12  // 电机3使能（PWM）
#define MOTOR4_EN 13  // 电机4使能（PWM）

// 超声波传感器引脚
#define ULTRA1_TRIG 22
#define ULTRA1_ECHO 23
#define ULTRA2_TRIG 24
#define ULTRA2_ECHO 25
#define ULTRA3_TRIG 26
#define ULTRA3_ECHO 27
#define ULTRA4_TRIG 28
#define ULTRA4_ECHO 29

// TFLuna LiDAR使用Serial2

// Qi无线充电控制引脚
#define CHARGE_CTRL 30
#define CHARGE_STATUS 31

// 电池电压检测引脚
#define BATTERY_PIN A0

// 全局变量
float ultrasonicDist[4];  // 超声波距离数据
float lidarDist;          // 激光测距数据
float batteryVoltage;     // 电池电压
bool isCharging;          // 充电状态

void setup() {
  // 初始化串口
  Serial.begin(115200);   // 与树莓派通信
  Serial2.begin(115200);  // 与TFLuna通信
  
  // 初始化电机控制引脚
  pinMode(MOTOR1_IN1, OUTPUT);
  pinMode(MOTOR1_IN2, OUTPUT);
  pinMode(MOTOR2_IN1, OUTPUT);
  pinMode(MOTOR2_IN2, OUTPUT);
  pinMode(MOTOR3_IN1, OUTPUT);
  pinMode(MOTOR3_IN2, OUTPUT);
  pinMode(MOTOR4_IN1, OUTPUT);
  pinMode(MOTOR4_IN2, OUTPUT);
  
  pinMode(MOTOR1_EN, OUTPUT);
  pinMode(MOTOR2_EN, OUTPUT);
  pinMode(MOTOR3_EN, OUTPUT);
  pinMode(MOTOR4_EN, OUTPUT);
  
  // 初始化超声波传感器引脚
  pinMode(ULTRA1_TRIG, OUTPUT);
  pinMode(ULTRA1_ECHO, INPUT);
  pinMode(ULTRA2_TRIG, OUTPUT);
  pinMode(ULTRA2_ECHO, INPUT);
  pinMode(ULTRA3_TRIG, OUTPUT);
  pinMode(ULTRA3_ECHO, INPUT);
  pinMode(ULTRA4_TRIG, OUTPUT);
  pinMode(ULTRA4_ECHO, INPUT);
  
  // 初始化充电控制
  pinMode(CHARGE_CTRL, OUTPUT);
  pinMode(CHARGE_STATUS, INPUT);
  digitalWrite(CHARGE_CTRL, LOW);
  
  // 停止所有电机
  stopMotors();
}

void loop() {
  // 检查串口命令
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    processCommand(cmd);
  }
  
  // 更新传感器数据
  updateSensors();
  
  // 短暂延时
  delay(10);
}

void processCommand(String cmd) {
  // 解析命令
  if (cmd.startsWith("M,")) {  // 电机控制命令
    // 格式：M,speed1,speed2,speed3,speed4
    cmd = cmd.substring(2);  // 移除"M,"
    int speeds[4];
    int index = 0;
    
    // 解析4个速度值
    while (cmd.length() > 0 && index < 4) {
      int commaPos = cmd.indexOf(',');
      if (commaPos == -1) {
        speeds[index] = cmd.toInt();
        break;
      } else {
        speeds[index] = cmd.substring(0, commaPos).toInt();
        cmd = cmd.substring(commaPos + 1);
        index++;
      }
    }
    
    // 设置电机速度
    setMotorSpeed(0, speeds[0]);
    setMotorSpeed(1, speeds[1]);
    setMotorSpeed(2, speeds[2]);
    setMotorSpeed(3, speeds[3]);
    
  } else if (cmd.startsWith("S")) {  // 请求传感器数据
    sendSensorData();
    
  } else if (cmd.startsWith("C,")) {  // 充电控制命令
    // 格式：C,1（开始充电）或C,0（停止充电）
    int state = cmd.substring(2).toInt();
    digitalWrite(CHARGE_CTRL, state ? HIGH : LOW);
  }
}

void setMotorSpeed(int motor, int speed) {
  // speed范围：-255到255
  speed = constrain(speed, -255, 255);
  
  // 选择对应的控制引脚
  int in1, in2, en;
  switch (motor) {
    case 0:
      in1 = MOTOR1_IN1;
      in2 = MOTOR1_IN2;
      en = MOTOR1_EN;
      break;
    case 1:
      in1 = MOTOR2_IN1;
      in2 = MOTOR2_IN2;
      en = MOTOR2_EN;
      break;
    case 2:
      in1 = MOTOR3_IN1;
      in2 = MOTOR3_IN2;
      en = MOTOR3_EN;
      break;
    case 3:
      in1 = MOTOR4_IN1;
      in2 = MOTOR4_IN2;
      en = MOTOR4_EN;
      break;
    default:
      return;
  }
  
  // 设置方向和速度
  if (speed > 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
    analogWrite(en, speed);
  } else if (speed < 0) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
    analogWrite(en, -speed);
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
    analogWrite(en, 0);
  }
}

void stopMotors() {
  for (int i = 0; i < 4; i++) {
    setMotorSpeed(i, 0);
  }
}

float readUltrasonic(int trigPin, int echoPin) {
  // 发送触发脉冲
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // 测量回波时间
  long duration = pulseIn(echoPin, HIGH);
  
  // 计算距离（厘米）
  return duration * 0.034 / 2.0;
}

float readLidar() {
  float distance = 0;
  
  // 检查TFLuna是否有数据
  if (Serial2.available() >= 9) {
    // TFLuna数据帧为9字节
    if (Serial2.read() == 0x59 && Serial2.read() == 0x59) {
      unsigned char buffer[7];
      Serial2.readBytes(buffer, 7);
      
      // 距离在第3、4字节
      distance = (buffer[1] << 8) + buffer[0];
    }
  }
  
  return distance;
}

float readBatteryVoltage() {
  // 读取电池电压
  int raw = analogRead(BATTERY_PIN);
  // 转换为实际电压（根据分压电路调整）
  return raw * (48.0 / 1023.0);
}

void updateUltrasonicSensors() {
  if (!useUltrasonic) return;
  
  // 更新4个超声波传感器数据
  ultrasonicDist[0] = getUltrasonicDistance(ULTRA1_TRIG, ULTRA1_ECHO);
  ultrasonicDist[1] = getUltrasonicDistance(ULTRA2_TRIG, ULTRA2_ECHO);
  ultrasonicDist[2] = getUltrasonicDistance(ULTRA3_TRIG, ULTRA3_ECHO);
  ultrasonicDist[3] = getUltrasonicDistance(ULTRA4_TRIG, ULTRA4_ECHO);
}

float getUltrasonicDistance(int trigPin, int echoPin) {
  // 发送触发信号
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // 读取回波时间并计算距离（厘米）
  float duration = pulseIn(echoPin, HIGH);
  return duration * 0.034 / 2.0;
}

void updateLidarSensor() {
  if (!useLidar) return;
  
  // 读取TFLuna数据
  if (Serial2.available() >= 9) {
    if (Serial2.read() == 0x59 && Serial2.read() == 0x59) {
      unsigned char buffer[7];
      Serial2.readBytes(buffer, 7);
      
      // 计算距离（厘米）
      lidarDist = buffer[0] + buffer[1] * 256;
    }
  }
}

void updateBatteryStatus() {
  // 读取电池电压
  int rawValue = analogRead(BATTERY_PIN);
  batteryVoltage = rawValue * (5.0 / 1023.0) * 11.0;  // 电压分压比例
  
  // 读取充电状态
  isCharging = digitalRead(CHARGE_STATUS) == HIGH;
}

void sendUltrasonicData() {
  Serial.print("US,");
  for (int i = 0; i < 4; i++) {
    Serial.print(ultrasonicDist[i]);
    if (i < 3) Serial.print(",");
  }
  Serial.println();
}

void sendLidarData() {
  Serial.print("LD,");
  Serial.println(lidarDist);
}

void sendBatteryData() {
  Serial.print("BAT,");
  Serial.print(batteryVoltage);
  Serial.print(",");
  Serial.println(isCharging ? "1" : "0");
}

void sendSensorData() {
  // 发送格式：DATA:u1,u2,u3,u4,l,b,c
  Serial.print("DATA:");
  
  // 发送超声波数据
  for (int i = 0; i < 4; i++) {
    Serial.print(ultrasonicDist[i]);
    Serial.print(',');
  }
  
  // 发送激光测距数据
  Serial.print(lidarDist);
  Serial.print(',');
  
  // 发送电池电压
  Serial.print(batteryVoltage);
  Serial.print(',');
  
  // 发送充电状态
  Serial.println(isCharging ? '1' : '0');
}