// import Nevow.Athena

if (typeof RoomWidget == 'undefined') {
    RoomWidget = {};
}

RoomWidget.Slider = Nevow.Athena.Widget.subclass('RoomWidget.Slider');
RoomWidget.Slider.methods(
    function __init__(self, node) {

      RoomWidget.Slider.upcall(self, '__init__', node);

      self.callRemote('getName').addCallback(function setupSlider(name) {
    
      self.slider = new Bs_Slider();
      s = self.slider;
      s.attachOnChange(function (sliderObj, val, newPos) {
	  self.callRemote('sliderChange', val);
      });
      s.fieldName     = name;
      s.width         = 49;
      s.height        = 15;
      s.minVal        = 0;
      s.maxVal        = 1;
      s.valueDefault  = 0;
      s.valueInterval = 0.15;
      s.imgDir = 'blueshoes/components/slider/img/';
      s.setBackgroundImage('increase/bg.gif', 'no-repeat');
      s.setSliderIcon('increase/knob.gif', 10, 21);
      s.useInputField = 0;
      s.draw(name);
      });
    },
    function setValue(self, val) {
      self.slider.setValue(val);
    });

function bsSliderChange(sliderObj, val, newPos){ 
    server.handle('sliderChange', sliderObj.fieldName, val);
}
