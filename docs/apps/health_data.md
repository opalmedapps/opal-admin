# Health Data App

The `health_data` app provides the ability to store different health data for patients.
The data usually comes from various smart devices and is provided by the patient directly through the mobile app.
It could also come from a clinician where the data might be entered manually.

The general design is that the models provide the data structure to support this.
An API allows the app to add new data.
And views allow clinicians to view the data.

## Data Design

The models are inspired by Apple's [HealthKit](https://developer.apple.com/documentation/healthkit).
It is currently a heavily simplified version of it.

The general model is a sample with common properties (derived from [AbstractSample][opal.health_data.models.AbstractSample]).
A [QuantitySample][opal.health_data.models.QuantitySample] represents numerical sample data.

For simplicity, units and devices are not represented as their own models currently.
This can be changed in the future if needed.
See below for future enhancements for more details.

Units are represented via an enum (`TextChoices`) for now.
This enforces one unit for a data type and means that any unit conversion needs to happen before data insertion.

### Future Enhancements

#### Samples

An additional data sample would definitely be electrocardiogram (ECG).
Since an ECG consists of a range of volt measurements over time (see [Electrocardiogram on HealthKit](https://developer.apple.com/documentation/healthkit/hkelectrocardiogram)) it requires its own model.

In addition, it needs to be determined how to design blood pressure.
Blood pressure consists of the systolic and diastolic blood pressure.
For example, HealthKit has [systolic](https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier/1615552-bloodpressuresystolic) and [diastolic](https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier/1615233-bloodpressurediastolic) blood pressure on its own but also the correlated [blood pressure](https://developer.apple.com/documentation/healthkit/hkcorrelationtypeidentifier/1615325-bloodpressure) combining the two.

#### Devices

The source device is currently a string which is whatever the device reports as its name.
Therefore, there is currently no knowledge about which patient has which device assigned.

In the future, devices could be added with various information, such as, manufacturer, serial number, model number etc.
For example, this would allow us to prevent data insertion for unknown devices.

#### Units

As mentioned above, specific units are currently enforced for each data type.
Similar to _HealthKit_ it would be possible to have a specific model for a unit and to assign such a unit to a data sample instance.
In addition, we could allow units to be converted.
This could be done for data insertion and/or data visualization.
For example, to allow a user to look at the weight either in kg or lbs.

For proper unit support there exists the [`pint` package](https://pint.readthedocs.io/en/stable/).
`pint` has full support for everything related to units.
Even custom units can be defined.

For instance, _beats per minute_ (bpm) does not exist by default.
It can be defined with the following unit definition:

```plain
minute = 60 * second = min
beats_per_minute = beat / minute = bpm
hertz = counts / second = hz
beat = [heart_beats] = b
```
