/* i2c.c */

/*
   This code was ported from DOS to Linux.
   Before running this code, access to printer port 1 should be gained with:

      ioperm(0x378, 3, 1) 

   It is fine to put this line in the beginning of main.  Remember that
   ioperm can only be set by a process with root privileges!

   Compile with: gcc -O3 -c i2c.c 

   Disclaimer: This software is free for distribution.  It has not been fully
   tested.  No guarantee is taken for its correct operation.  No
   responsibility is taken for damage to components, software or anything
   else, as a result of using this software.
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/io.h>

#define MaxIOcard 3
#define MaxIOchip 7
#define MaxIOchannel 64
#define MaxDACchannel 32
#define MaxADchannel 16
#define MaxDAchannel 4

extern char *Bin;

short IOchipCode[] = {0x70, 0x72, 0x74, 0x76, 0x78, 0x7A, 0x7C, 0x7E};
short DACchipCode[] = {0x40, 0x42, 0x44, 0x46};
short ADDAchipCode[] = {0x90, 0x92, 0x94, 0x96};

short IOconfig[MaxIOchip+1];
short IOdata[MaxIOchip+1];
short IO[MaxIOchannel+1];
short DAC[MaxDACchannel+1];
short AD[MaxADchannel+1];
short DA[MaxDAchannel+1];
short ControlPort;
short StatusPort;
short I2CbusDelay;

/*DOS2LINUX CONVERSION PROCEDURES*/
void outport(int port, int value);

/*CLOSED PROCEDURES*/
void ReadIOchip(int Chip_no);

/*IO CONFIGURATION PROCEDURES*/
void ConfigAllIOasInput(void);
void ConfigAllIOasOutput(void);
void ConfigIOchipAsInput(int Chip_no);
void ConfigIOchipAsOutput(int Chip_no);
void ConfigIOchannelAsInput(int Channel_no);
void ConfigIOchannelAsOutput(int Channel_no);

/*UPDATE IOdata & IO ARRAY PROCEDURES*/
void UpdateIOdataArray(int Chip_no, int Data);
void ClearIOdataArray(int Chip_no);
void SetIOdataArray(int Chip_no);
void SetIOchArray(int Channel_no);
void ClearIOchArray(int Channel_no);

/*OUTPUT PROCEDURES*/
void IOoutput(int Chip_no, int Data);
void UpdateAllIO(void);
void ClearAllIO(void);
void SetAllIO(void);
void UpdateIOchip(int Chip_no);
void ClearIOchip(int Chip_no);
void SetIOchip(int Chip_no);
void SetIOchannel(int Channel_no);
void ClearIOchannel(int Channel_no);

/*INPUT PROCEDURES*/
int ReadIOchannel(int Channel_no);

/*6 BIT DAC CONVERTER PROCEDURES*/
void OutputDACchannel(int Channel_no, int Data);
void UpdateDACchannel(int Channel_no);
void ClearDACchannel(int Channel_no);
void SetDACchannel(int Channel_no);
void UpdateDACchip(int Chip_no);
void ClearDACchip(int Chip_no);
void SetDACchip(int Chip_no);
void UpdateAllDAC(void);
void ClearAllDAC(void);
void SetAllDAC(void);

/*8 BIT DA CONVERTER PROCEDURES*/
void OutputDAchannel(int Channel_no, int Data);
void UpdateDAchannel(int Channel_no);
void ClearDAchannel(int Channel_no);
void SetDAchannel(int Channel_no);
void UpdateAllDA(void);
void ClearAllDA(void);
void SetAllDA(void);

/*8 BIT AD CONVERTER PROCEDURES*/
int ReadADchannel(int Channel_no);

/*I2C BUS CONDITIONS*/
void SelectI2CprinterPort(int Printer_no);
void I2CBusNotBusy(void);


/*
        **********************************
	* DOS2LINUX CONVERSION PROCEDURE *
	**********************************
*/
void outport(int port, int value)
{
  outb (value, port);  /* redirect low level output */
}

/*	*******************************
	* IO CONFIGURATION PROCEDURES *
	*******************************

	Config all IO-ports as inputs (1 = Input mode / 0 = Output Mode).
	-----------------------------------------------------------------
*/
void ConfigAllIOasInput()
{
	int Chip_no;

	for (Chip_no = 0; Chip_no <= MaxIOchip; Chip_no++) {
		IOconfig[Chip_no] = 0;		/*Config all IO-ports as outputs*/
		ClearIOchip(Chip_no);		/*Clear all IO-ports*/
		IOconfig[Chip_no] = 0xFF;	/*Config all IO-ports as inputs*/
		ReadIOchip(Chip_no);		/*Update 'IOdata' & 'IO' array*/
	}
};

/*
	Config all IO-ports as outputs (1 = Input mode / 0 = Output Mode).
	-----------------------------------------------------------------
*/
void ConfigAllIOasOutput()
{
	int Chip_no;

	for (Chip_no = 0; Chip_no <= MaxIOchip; Chip_no++)
		IOconfig[Chip_no] = 0x00;	/*Config all IO-ports as outputs*/
	ClearAllIO();				/*Clear all IO-ports*/
};

/*
	Config one IO-port as input (1 = Input mode / 0 = Output mode).
	---------------------------------------------------------------
*/
void ConfigIOchipAsInput(int Chip_no)
{
	IOconfig[Chip_no] = 0;		/*Config IO-port as output*/
	ClearIOchip(Chip_no);		/*Clear  IO-port*/
	IOconfig[Chip_no] = 0xFF;	/*Config IO-port as inputs*/
	ReadIOchip(Chip_no);		/*Update 'IOdata' & 'IO' array*/
};

/*
	Config one IO-port as output (1 = Input mode / 0 = Output mode).
	----------------------------------------------------------------
*/
void ConfigIOchipAsOutput(int Chip_no)
{
	IOconfig[Chip_no] = 0x00;	/*IO-port as outputs*/
	ClearIOchip(Chip_no);		/*Clear IO-port*/
};

/*
	Config one IO-channel as input (1 = Input mode / 0 = Output mode).
	------------------------------------------------------------------
*/
void ConfigIOchannelAsInput(int Channel_no)
{
	int Chip_no, Channel;

	Chip_no = (Channel_no - 1) / 8;		/*Calculate chip no*/
	Channel = (Channel_no - 1) % 8;		/*Calculate channel from IOchip*/
	IOconfig[Chip_no] = IOconfig[Chip_no] & (~(0x01 << Channel)); /*Set IOchannel as output*/
	ClearIOchannel(Channel_no);			/*clear IO-channel*/
	IOconfig[Chip_no] = IOconfig[Chip_no] | (0x01 << Channel); /*Set IOchannel as input*/
	ReadIOchannel(Channel_no);			/*Update 'IOdata' & 'IO' array*/
};

/*
	Config one IO-channel as output (1 = Input mode / 0 = Output mode).
	-------------------------------------------------------------------
*/
void ConfigIOchannelAsOutput(int Channel_no)
{
	int Chip_no, Channel;

	Chip_no = (Channel_no - 1) / 8;		/*Calculate chip no*/
	Channel = (Channel_no - 1) % 8;		/*Calculate channel from IOchip*/
	IOconfig[Chip_no] = IOconfig[Chip_no] & (~(0x01 << Channel)); /*Set IOchannel as output*/
	ClearIOchannel(Channel_no);			/*clear IO-channel*/
};

/*
	*****************************************
	* UPDATE IOdata & IO ARRAY PROCEDURES *
	*****************************************

	Update the 'IOdata' & 'IO' array with data for selected chip.
	-------------------------------------------------------------
*/

void UpdateIOdataArray(int Chip_no, int Data)
{
	int Start_Channel, Channel;

	/*Update 'IOdata' array*/
	IOdata[Chip_no] = (IOdata[Chip_no] & IOconfig[Chip_no]);
	IOdata[Chip_no] = IOdata[Chip_no] | (Data & (~IOconfig[Chip_no]));
	/*Update 'IO' array*/
	Start_Channel = Chip_no * 8 + 1;	/*Calculate start channel*/
	for (Channel = 0; Channel <= 7; Channel++)	/*Test status 8 ch. of the IOchip*/
		IO[Start_Channel+Channel] = ((IOdata[Chip_no] & (0x01 << Channel)) != 0);
};

/*
	Clear the 'IOdata' & 'IO' array from the selected chip.
	-------------------------------------------------------
*/
void ClearIOdataArray(int Chip_no)
{
	int Start_Channel, Channel;

	/*Update 'IOdata' array*/
	IOdata[Chip_no] = IOdata[Chip_no] & IOconfig[Chip_no];
	/*Update 'IO' array*/
	Start_Channel = Chip_no * 8 + 1;	/*Calculate start channel*/
	for (Channel = 0; Channel <= 7; Channel++)	/*Test status 8 ch. of the IOchip*/
		IO[Start_Channel+Channel] = ((IOdata[Chip_no] & (0x01 << Channel)) != 0);
};

/*
	Setthe 'IOdata' & 'IO' array from the selected chip.
	----------------------------------------------------
*/
void SetIOdataArray(int Chip_no)
{
	int Start_Channel, Channel;

	/*Update 'IOdata' array*/
	IOdata[Chip_no] = IOdata[Chip_no] | ( ~IOconfig[Chip_no]);
	/*Update 'IO' array*/
	Start_Channel = Chip_no * 8 + 1;		/*Calculate start channel*/
	for (Channel = 0; Channel <= 7; Channel++)	/*Test status 8 ch. of the IOchip*/
		IO[Start_Channel+Channel] = ((IOdata[Chip_no] & (0x01 << Channel)) != 0);
};

/*
	Set the 'IOdata' & 'IO' array from the selected channel.
	--------------------------------------------------------
*/
void SetIOchArray(int Channel_no)
{
	int Chip_no, Channel, Data;

	Chip_no = (Channel_no - 1) / 8;		/*Calculate chip no*/
	Channel = (Channel_no - 1) % 8;		/*Calculate channel of IOchip*/
	Data = IOdata[Chip_no] | (0x01 << Channel);	/*Data for correct IOchannel to set*/
	UpdateIOdataArray(Chip_no, Data);		/*Update IOdata & IO array*/
};

/*
	Clear the 'IOdata' & 'IO' array from the selected channel.
	----------------------------------------------------------
*/
void ClearIOchArray(int Channel_no)
{
	int Chip_no, Channel, Data;

	Chip_no = (Channel_no - 1) / 8;		/*Calculate chip no*/
	Channel = (Channel_no - 1) % 8;		/*Calculate channel of IOchip*/
	Data = IOdata[Chip_no] & (~(0x01 << Channel));	/*Data for IOchannel to clear*/
	UpdateIOdataArray(Chip_no, Data);		/*Update IOdata & IO array*/
};
/*
	*********************
	* OUTPUT PROCEDURES *
	*********************

	Output data to selected IO-port and update the 'IOdata' & 'IO' array.
	---------------------------------------------------------------------
*/
void IOoutput(int Chip_no, int Data)
{
        /* make sure the following ints are represented in 16 bit */
	short Start_Channel, Channel, cport, i, j, SerData; 

	Data = (~Data) | IOconfig[Chip_no];	/*Mask input channels*/

	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode*/
	SerData = (IOchipCode[Chip_no] << 8);     	/*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {

/*cport = (SerData < 0) ? 0x0C: 0x0E;*/
                cport = (SerData < 0) ? 0xCC: 0xCE;

		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of data*/
	SerData = (Data << 8);
	for (j = 1; j <= 8; j++) {
/*cport = (SerData < 0) ? 0x0C: 0x0E;*/
		cport = (SerData < 0) ? 0xCC: 0xCE;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Update 'IOdata' array*/
	IOdata[Chip_no] = (IOdata[Chip_no] & IOconfig[Chip_no]) | (~Data);

	/*Update 'IO' array*/
	Start_Channel = Chip_no * 8 + 1;		/*Calculate start channel*/
	for (Channel = 0; Channel <= 7; Channel++)	/*Test status 8 ch. of the IOchip*/
		IO[Start_Channel+Channel] = ((IOdata[Chip_no] & (0x01 << Channel)) != 0);
};

/*
	Update all IO channels with value stored into the 'IOdata' array.
	-----------------------------------------------------------------
*/
void UpdateAllIO()
{
	int Chip_no;

	for (Chip_no = 0; Chip_no <= MaxIOchip; Chip_no++)
		IOoutput(Chip_no, IOdata[Chip_no]);	/*Update all IO-ports*/
};

/*
	Clear all IO channels and update the 'IOdata' & 'IO' array.
	-----------------------------------------------------------
*/
void ClearAllIO()
{
	int Chip_no;

	for (Chip_no = 0; Chip_no <= MaxIOchip; Chip_no++)
		IOoutput(Chip_no, 0);	/*Clear all IO-port*/
};

/*
	Set all IO channels and update the 'IOdata' & 'IO' array.
	---------------------------------------------------------
*/
void SetAllIO()
{
	int Chip_no;

	for (Chip_no = 0; Chip_no <= MaxIOchip; Chip_no++)
		IOoutput(Chip_no, 0x0FF);	/*Set all IO-port*/
};

/*
	Update IO chip with value stored into the 'IOdata' array.
	---------------------------------------------------------
*/
void UpdateIOchip(int Chip_no)
{
	IOoutput(Chip_no, IOdata[Chip_no]);	/*Update IO port*/
};

/*
	Clear IO chip and update the 'IOdata' & 'IO' array.
	---------------------------------------------------
*/
void ClearIOchip(int Chip_no)
{
	IOoutput(Chip_no, 0);	/*Clear IO-port*/
};

/*
	Set IO chip and update the 'IOdata' & 'IO' array.
	-------------------------------------------------
*/
void SetIOchip(int Chip_no)
{
	IOoutput(Chip_no, 0x0FF);	/*Set IO-port*/
};

/*
	Set one IO channel and update the 'IOdata' & 'IO' array.
	--------------------------------------------------------
*/
void SetIOchannel(int Channel_no)
{
	int Chip_no, Channel, Data;

	Chip_no = (Channel_no - 1) / 8;		/*Calculate chip no*/
	Channel = (Channel_no - 1) % 8;		/*Calculate channel of IOchip*/
	Data = IOdata[Chip_no] | (0x01 << Channel);	/*Data for correct IOchannel to set*/
	IOoutput(Chip_no, Data);			/*Set IOchannel*/
};

/*
	Clear one IO channel and update the 'IOdata' & 'IO' array.
	----------------------------------------------------------
*/
void ClearIOchannel(int Channel_no)
{
	int Chip_no, Channel, Data;

	Chip_no = (Channel_no - 1) / 8;		/*Calculate chip no*/
	Channel = (Channel_no - 1) % 8;		/*Calculate channel of IOchip*/
	Data = IOdata[Chip_no] & (~(0x01 << Channel));	/*Data for IOchannel to clear*/
	IOoutput(Chip_no, Data);			/*Clear IOchannel*/
};

/*
	*********************
	* INPUT PROCEDURES  *
	*********************

	Read IO chip and update the 'IOdata' & 'IO' array.
	--------------------------------------------------
*/
void ReadIOchip(int Chip_no)
{
        /* Make sure the following ints are represented in 16 bit */
	short Start_Channel, Channel, Data, cport, i, j;

	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode for readmode*/
	Data = ((IOchipCode[Chip_no] | 0x01) << 8);  /*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (Data < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		Data <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial input of ChipData*/
	Data = 0;				/*Clear Data*/
	for (j = 1; j <= 8; j++) {
		Data <<= 1;
		outport(ControlPort, 0x04);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
		if (inb(StatusPort) & 0x10) Data = Data | 0x0001;
		outport(ControlPort, 0x0C);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	};
	IOdata[Chip_no] = ~Data;

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Update 'IO' array*/
	Start_Channel = Chip_no * 8 + 1;	/*Calculate start channel*/
	for (Channel = 0; Channel <= 7; Channel++)	/*Test status 8 ch. of the IOchip*/
		IO[Start_Channel+Channel] = ((IOdata[Chip_no] & (0x01 << Channel)) != 0);
};

/*
	Read all IO channels and update the 'IOdata' & 'IO' array.
	----------------------------------------------------------
*/
void ReadAllIO()
{
	int Chip_no;

	for (Chip_no = 0; Chip_no <= MaxIOchip; Chip_no++)
		ReadIOchip(Chip_no);	/*Read all IO ports*/
};

/*
	Read one IO channels and update the 'IOdata' & 'IO' array.
	----------------------------------------------------------
*/
int ReadIOchannel(int Channel_no)
{
	int Chip_no;

	Chip_no = (Channel_no - 1) / 8;	/*Calculate chip no*/
	ReadIOchip(Chip_no);			/*Read IO port*/
        return IO[Channel_no];
};

/*
	**********************************
	* 6 BIT DAC CONVERTER PROCEDURES *
	**********************************

	Set selected DAC channel by given value. The 'DAC' array will be updated.
	-------------------------------------------------------------------------
*/
void OutputDACchannel(int Channel_no, int Data)
{
        /* make sure the following ints are represented in 16 bit */
	short SerData, cport, i, j;

	Data = (Data > 63) ? 63: Data;	/*If overflow  set at maximum (63)*/
	DAC[Channel_no] = Data;	/*Update 'DAC' array*/

	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode*/
	SerData = ((DACchipCode[(Channel_no - 1) / 8]) << 8);	/*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (SerData < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of selected channel*/
	SerData = ((0xF0 | ((Channel_no - 1) % 8)) << 8);	/*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (SerData < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Data*/
	SerData = (Data << 8);
	for (j = 1; j <= 8; j++) {
		cport = (SerData < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
};

/*
	Update the eight DAC channels from the selected chip by the 'DAC' array.
	------------------------------------------------------------------------
*/
void UpdateDACchip(int Chip_no)
{
        /* make sure the following ints are represented in 16 bit */
	short SerData, i, j, Channel, k, cport;

	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode*/
	SerData = (DACchipCode[Chip_no] << 8);    /*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
                cport = (SerData < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
        	for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of channel 0 from selected chip*/
	SerData = (0x00);
	for (j = 1; j <= 8; j++) {
                cport = (SerData < 0) ? 0x0C: 0x0E;
        	outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Update the 8 channels of the selected chip*/
	Channel = Chip_no * 8;				/*Calculate DAC channel*/
	for (k = 1; k <= 8; k++) {
		/*Serial output of DAC Data*/
		DAC[Channel + k] = (DAC[Channel+k] > 63) ? 63 : DAC[Channel+k];	/*Overflow*/
		/*Shift data 8 bits left*/
		SerData = (DAC[Channel + k] << 8);
		for (j = 1; j <= 8; j++) {
/*cport = (SerData < 0) ? 0x0C: 0x0E;*/ 
                        cport = (SerData < 0) ? 0x0C: 0x0E;
			outport(ControlPort, cport);
			for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
			cport = cport & 0x07;
			outport(ControlPort, cport);
			SerData <<= 1;
			for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
			cport = cport | 0x08;
			outport(ControlPort, cport);
			for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		};

		/*Clock pulse for acknowledgement*/
		outport(ControlPort, 0x0C);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
		outport(ControlPort, 0x04);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
		outport(ControlPort, 0x0C);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	};

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
};

/*
	Update DAC channels by the 'DA' array.
	--------------------------------------
*/
void UpdateDACchannel(int Channel_no)
{
	OutputDACchannel(Channel_no, DAC[Channel_no]); /*Update DAC channel*/
};

/*
	Set selected DAC channel at minimum (0). The 'DAC' array will be updated.
	-------------------------------------------------------------------------
*/
void ClearDACchannel(int Channel_no)
{
	OutputDACchannel(Channel_no, 0); /*Set selected DAC channel at 0*/
};

/*
	Set selected DAC channel at maximum (63). The 'DAC' array will be updated.
	--------------------------------------------------------------------------
*/
void SetDACchannel(int Channel_no)
{
	OutputDACchannel(Channel_no,63);  /*Set selected DAC channel at 63*/
};

/*
	Set the eight DAC channels from the selected chip at minimum (0) and update the 'DAC' array.
	--------------------------------------------------------------------------------------------
*/
void ClearDACchip(int Chip_no)
{
	int i, Channel;

	Channel = Chip_no * 8;
	for (i = 1; i <= 8; i++)
		DAC[Channel + i] = 0;	/*Clear 8 channels of selected chip*/
	UpdateDACchip(Chip_no);		/*Update DAC chip*/
};

/*
	Set the eight DAC channels from the selected chip at maximum (63) and update the 'DAC' array.
	---------------------------------------------------------------------------------------------
*/
void SetDACchip(int Chip_no)
{
	int i, Channel;

	Channel = Chip_no * 8;
	for (i = 1; i <= 8; i++)
		DAC[Channel + i] = 63;	/*Set 8 channels selected chip max*/
	UpdateDACchip(Chip_no);		/*Update DAC chip*/
};

/*
	Update all DAC channels by the 'DAC' array.
	-------------------------------------------
*/
void UpdateAllDAC()
{
	int Chip_no;

	for (Chip_no = 0; Chip_no <= MaxIOcard; Chip_no++)
		UpdateDACchip(Chip_no);	/*Update all DAC channels*/
};

/*
	Set all DAC channels at minimum (0) and update the 'DAC' array.
	---------------------------------------------------------------
*/
void ClearAllDAC()
{
	int Channel_no;

	for (Channel_no = 1; Channel_no <= MaxDACchannel; Channel_no++)
		DAC[Channel_no] = 0x00;	/*Clear the 'DAC' array*/
	UpdateAllDAC();				/*Update all DAC channels*/
};

/*
	Set all DAC channels at maximum (63) and update the 'DAC' array.
	----------------------------------------------------------------
*/
void SetAllDAC()
{
	int Channel_no;

	for (Channel_no = 1; Channel_no <= MaxDACchannel; Channel_no++)
		DAC[Channel_no] = 63;	/*Set 'DAC' array at max.(63)*/
	UpdateAllDAC();			/*Update all DAC channels*/
};

/*
	*********************************
	* 8 BIT DA CONVERTER PROCEDURES *
	*********************************

	Set selected DA channel by given value. The 'DA' array will be updated.
	-----------------------------------------------------------------------
*/
void OutputDAchannel(int Channel_no, int Data)
{
        /* make sure the following ints are represented in 16 bit */
	short SerData, cport, i, j;

	DA[Channel_no] = Data;	/*Store DA data into DA array*/

	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode*/
	SerData = ((ADDAchipCode[Channel_no-1] << 8));	/*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (SerData < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of ControlByte*/
	SerData = (0x40 << 8);
	for (j = 1; j <= 8; j++) {
		cport = (SerData < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of DA Data*/
	SerData = (Data << 8);
	for (j = 1; j <= 8; j++) {
		cport = (SerData < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		SerData <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
};

/*
	Update DA channels by the 'DA' array .
	--------------------------------------
*/
void UpdateDAchannel(int Channel_no)
{
	OutputDAchannel(Channel_no, DA[Channel_no]);	/*Update DA channel */
};

/*
	Set selected DA channel at minimum (0). The 'DA' array will be updated.
	-----------------------------------------------------------------------
*/
void ClearDAchannel(int Channel_no)
{
	OutputDAchannel(Channel_no, 0);	/*Set selected DA channel at 0*/
};

/*
	Set selected DA channel at maximum (255). The 'DA' array will be updated.
	-------------------------------------------------------------------------
*/
void SetDAchannel(int Channel_no)
{
	OutputDAchannel(Channel_no, 255);	/*Set selected DA channel at 255*/
};

/*
	Update all DA channels by the 'DA' array .
	------------------------------------------
*/
void UpdateAllDA()
{
	int Channel_no;

	for (Channel_no = 1; Channel_no <= MaxDAchannel; Channel_no++)
		OutputDAchannel(Channel_no, DA[Channel_no]);	/*Update all DA channels*/
};

/*
	Set all DA channels at minimum (0). The 'DA' array will be cleared.
	-------------------------------------------------------------------
*/
void ClearAllDA()
{
	int channel_no;

	for (channel_no = 1; channel_no <= MaxDAchannel; channel_no++)
		OutputDAchannel(channel_no, 0);	/*Set all DA channels at 0*/
};

/*
	Set all DA channels at maximum (255). The 'DA' array will be updated.
	---------------------------------------------------------------------
*/
void SetAllDA()
{
	int Channel_no;

	for (Channel_no = 1; Channel_no <= MaxDAchannel; Channel_no++ )
		OutputDAchannel(Channel_no, 255);			/*Set all DA channels at 255*/
};

/*
	*********************************************
	* 8 bit AD CONVERTER FUNCTIONS & PROCEDURES *
	*********************************************

	Read one AD channel. The result will be stored into the 'AD' array.
	-------------------------------------------------------------------
*/
int ReadADchannel(int Channel_no)
{
        /* make sure the following ints are represented in 16 bit */
	short ChipCode,i,j,cport,Data;

	ChipCode = ADDAchipCode[(Channel_no - 1) / 4];	/*Calculate chipcode*/

	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode*/
	Data = (ChipCode << 8);				/*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (Data < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		Data <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};


	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of selected channel*/
	Data = ((0x40 | ((Channel_no - 1) % 4)) << 8);	/*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (Data < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		Data <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode for readmode*/
	Data = ((ChipCode | 0x01) << 8);		        /*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (Data < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		Data <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial input of previous converted byte*/
	Data = 0;				/*Clear Data*/
	for (j = 1; j <= 8; j++) {
		Data <<= 1;
		outport(ControlPort, 0x04);
		
		// we really need some busywork here for a little delay
		for (i = 0; i <= 100; i++) {j=j+1;};    /*I2c-bus timing*/
		for (i = 0; i <= 100; i++) {j=j-1;};    /*I2c-bus timing*/

		if (inb(StatusPort) & 0x10) Data = Data | 0x0001;
		outport(ControlPort, 0x0C);
		//for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement from master*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};     /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};     /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};     /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};     /*I2c-bus timing*/

	/*Serial input of current converted byte*/
	Data = 0;				/*Clear Data*/
	for (j = 1; j <= 8; j++) {
		Data <<= 1;
		outport(ControlPort, 0x04);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
		if (inb(StatusPort) & 0x10) Data = Data | 0x0001;
		outport(ControlPort, 0x0C);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	};
	AD[Channel_no] = Data;			/*Store result*/

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
        return Data;
};

/*
	Read four AD channels from one chip. The result will be stored into the 'AD' array.
	-----------------------------------------------------------------------------------
*/
void ReadADchip(int Chip_no)
{
        /* make sure the following ints are represented in 16 bit */
	short Channel, k, j, i, Data, cport;

	Channel = Chip_no * 4 + 1;	/*Calculate first channel*/
																										/*Generate start condition*/
	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode*/
	Data = (ADDAchipCode[Chip_no] << 8);	/*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (Data < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		Data <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of controlbyte for autoincrement*/
	Data = (0x44 << 8);
	for (j = 1; j <= 8; j++) {
		cport = (Data < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		Data <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate start condition*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial output of Chipcode for readmode*/
	Data = ((ADDAchipCode[Chip_no] | 0x01) << 8);	/*Shift data 8 bits left*/
	for (j = 1; j <= 8; j++) {
		cport = (Data < 0) ? 0x0C: 0x0E;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport & 0x07;
		outport(ControlPort, cport);
		Data <<= 1;
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
		cport = cport | 0x08;
		outport(ControlPort, cport);
		for (i = 0; i <= I2CbusDelay; i++) {};  /*I2c-bus timing*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Serial input of previous converted byte*/
	Data = 0;				/*Clear Data*/
	for (j = 1; j <= 8; j++) {
		Data <<= 1;
		outport(ControlPort, 0x04);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
		if (inb(StatusPort) & 0x10) Data = Data | 0x0001;
		outport(ControlPort, 0x0C);
		for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	};

	/*Read 4 AD channels*/
	for (k = 0; k <= 3; k++) {
		/*ACKnowledge from MASTER*/
		outport(ControlPort, 0x0E);
		for (i = 0; i <= I2CbusDelay; i++) {};     /*I2c-bus timing*/
		outport(ControlPort, 0x06);
		for (i = 0; i <= I2CbusDelay; i++) {};     /*I2c-bus timing*/
		outport(ControlPort, 0x0E);
		for (i = 0; i <= I2CbusDelay; i++) {};     /*I2c-bus timing*/
		outport(ControlPort, 0x0C);
		for (i = 0; i <= I2CbusDelay; i++) {};     /*I2c-bus timing*/
		/*Serial input of current converted byte*/
		Data = 0;				/*Clear Data*/
		for (j = 1; j <= 8; j++) {
			Data <<= 1;
			outport(ControlPort, 0x04);
			for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
			if (inb(StatusPort) & 0x10) Data = Data | 0x0001;
			outport(ControlPort, 0x0C);
			for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
		};
		AD[Channel + k] = Data;	/*Store data*/
	};

	/*Clock pulse for acknowledgement*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x0C);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/

	/*Generate stop condition*/
	outport(ControlPort, 0x0E);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x06);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
	outport(ControlPort, 0x04);
	for (i = 0; i <= I2CbusDelay; i++) {};    /*I2c-bus timing*/
};

/*
	Read all AD channels. The result will be stored into the 'AD' array.
	--------------------------------------------------------------------
*/
void ReadAllAD()
{
	int Chip_no;
					/*Scanning of all AD chips*/
	for (Chip_no = 0; Chip_no <= MaxIOcard; Chip_no++)
		ReadADchip(Chip_no);	/*Read 4 AD channels from chip*/
};

/*
	****************************
	* COMPLETE CARD PROCEDURES *
	****************************

	Read all IO's & AD's and update 'IOdata', 'IO' & 'AD' arrays.
  -------------------------------------------------------------
*/
void ReadAll()
{
	ReadAllIO();	/*Read all IO ports*/
	ReadAllAD();	/*Read all DA channels*/
};

/*
	Read all IO's & AD's from one card and update 'IOdata', 'IO' & 'AD' arrays.
  ---------------------------------------------------------------------------
*/
void ReadCard(int Card_no)
{
	int Chip_no;

	Chip_no = Card_no * 2;		/*Calculate IO chip no*/
	ReadIOchip(Chip_no);		/*Read first  8 IO ports*/
	ReadIOchip(Chip_no + 1);	/*Read second 8 IO ports*/
	ReadADchip(Card_no);		/*Read 4 DA channels*/
};

/*
	Update all IO's, DAC's & DA's and update 'IOdata', 'IO', 'DAC' & 'DA' arrays.
	-----------------------------------------------------------------------------
*/
void UpdateAll()
{
	UpdateAllIO();	/*Update all IO ports*/
	UpdateAllDAC();	/*Update all DAC channels*/
	UpdateAllDA();	/*Update all DA channels*/
};

/*
	Update all IO DAC & DA's from one card and update 'IOdata' 'IO' 'DAC' 'DA' arrays.
  ----------------------------------------------------------------------------------
*/
void UpdateCard(int Card_no)
{
	int Chip_no;

	Chip_no = Card_no * 2;		/*Calculate chip no*/
	UpdateIOchip(Chip_no);		/*Update first  8 IO ports*/
	UpdateIOchip(Chip_no + 1);	/*Update second 8 IO ports*/
	UpdateDACchip(Card_no);		/*Update 8 DAC channels*/
	UpdateDAchannel(Card_no + 1);	/*Update DA channel*/
};

/*
	**********************
	* I2C-BUS CONDITIONS *
	**********************

	SDA IN  =  SELECT    (pin 13) = bit 4 of STATUSPORT
	SDA OUT = -AUTOFEED  (pin 14) = bit 1 of CONTROLPORT
	SCL OUT = -SELECT IN (pin 17) = bit 3 of CONTROLPORT bits 0,4...7 = 0 / bit 2 = 1  of CONTROLPORT

	Set I2C-bus at non actif.
	-------------------------
*/
void I2CBusNotBusy()
{
	outport(ControlPort, 0x04);	/*SDA & SCL HIGH*/
};

/*
	Select I2C communication printerport.
	-------------------------------------
*/

void SelectI2CprinterPort(int Printer_no)
{
	switch (Printer_no) {
		case 0: /*lpt on monochroom display adapter*/
			StatusPort  = 0x03BD;
			ControlPort = 0x03BE;
			break;
		case 1:	/*lpt1 on mainboard*/
			StatusPort  = 0x0379;
			ControlPort = 0x037A;
			break;
		case 2:	/*lpt2 on mainboard*/
			StatusPort  = 0x0279;
			ControlPort = 0x027A;
			break;
	};
	fprintf(stderr,"status port is %X\n",StatusPort);
};

/*
	***********************
	* INITIALIZATION PART *
	***********************
*/
void initialize()
{
	SelectI2CprinterPort(1);	/*Select LPT1 on mainboard*/
	I2CbusDelay = 1;		/*I2C-bus speed control factor*/
	I2CBusNotBusy();

};
#ifndef IN_PYTHON_MODULE
void main() 
{
  int prev=0,sw=0,lev=0;
  ioperm(0x378, 3, 1) ;
  fprintf(stderr,"opening 0x378 for io\n");
  initialize();
  ConfigAllIOasInput();
  ConfigIOchannelAsOutput(6);

  while(1) {
   ReadAll();
   sw = ReadIOchannel(12) | ReadIOchannel(9) | ReadIOchannel(10) | ReadIOchannel(11);
   if( sw!=prev ) {
     prev=sw;
     if( sw ) {
       lev=(lev-1)%8;
       OutputDACchannel(5,lev*8);
       OutputDACchannel(1,lev*8);
       OutputDACchannel(2,lev*8);
       OutputDACchannel(3,lev*8);
       OutputDACchannel(4,lev*8);
       lev>5?SetIOchannel(6):ClearIOchannel(6);
       UpdateAllDAC();
       UpdateIOchip(0);
     }
   }
   usleep(100000);
 }
}
#endif

