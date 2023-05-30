## Checklist
- [ ] version 1.1 and 2.0 need YUV colour space! implement on car.py
- [ ] angle smoothing on car.
- [ ] change collect.py to work with both degrees / radians (currently radians)

## Untested Model Notes
- 1.1
	- nvidia's dave-2
	- r^2 of ~75% 
	- on radian data
	- 10 epochs at 300 SPE, 200 VSPE, batch size 100.
	- test results:
		- 

- 2.0
	- custom architecture
	- r^2 of 95.7%
	- mse of 0.0024 
	- radian data
	- 10 epochs at 300 SPE, 200 VSPE, batch size 100.
	- test results:
		- 

- 2.1
	- custom architecture WITH DROPOUT LAYER. 
	- r^2 of 90.38%
	- mse of 0.0064
	- radian data
	- 10 epochs at 200 SPE, 150 VSPE, batch size 128. 
	- all augmentation enabled except for flip. 
	- test results:
		- 
