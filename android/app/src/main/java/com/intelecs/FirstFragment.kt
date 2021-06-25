package com.intelecs

import android.R
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.amazonaws.auth.CognitoCachingCredentialsProvider
import com.amazonaws.mobileconnectors.iot.AWSIotMqttClientStatusCallback
import com.amazonaws.mobileconnectors.iot.AWSIotMqttManager
import com.amazonaws.mobileconnectors.iot.AWSIotMqttQos
import com.amazonaws.regions.Regions
import com.google.android.material.shape.CornerFamily
import com.google.gson.Gson
import com.intelecs.databinding.FragmentFirstBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.MainScope
import kotlinx.coroutines.launch
import java.io.UnsupportedEncodingException
import java.nio.charset.Charset
import kotlin.math.round


/**
 * A simple [Fragment] subclass as the default destination in the navigation.
 */
class FirstFragment : Fragment(), CoroutineScope by MainScope() {

    private val IOT_CORE_TOPIC = "espthemostat/temp"
    private val LOG_TAG = "IoTCore"
    private val INVALID_TEMP = -273.15

    private lateinit var cognitoCredentials: CognitoCachingCredentialsProvider
    private lateinit var mqttManager: AWSIotMqttManager
    private var _binding: FragmentFirstBinding? = null

    private var lastData = DeviceTemperature(0.0, 0)

    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {

        _binding = FragmentFirstBinding.inflate(inflater, container, false)
        _binding?.cardOne?.let {

            it.shapeAppearanceModel = it.shapeAppearanceModel
                .toBuilder()
                .setTopLeftCorner(CornerFamily.ROUNDED, 30f)
                .setTopRightCorner(CornerFamily.ROUNDED, 60f)
                .setBottomRightCorner(CornerFamily.ROUNDED, 30f)
                .setBottomLeftCorner(CornerFamily.ROUNDED, 60f)
                .build()
        }
_binding?.cardTwo?.let {

            it.shapeAppearanceModel = it.shapeAppearanceModel
                .toBuilder()
                .setTopLeftCorner(CornerFamily.ROUNDED, 60f)
                .setTopRightCorner(CornerFamily.ROUNDED, 30f)
                .setBottomRightCorner(CornerFamily.ROUNDED, 60f)
                .setBottomLeftCorner(CornerFamily.ROUNDED, 30f)
                .build()
        }

        return binding.root

    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)



        connectToIoT()

//        binding.buttonFirst.setOnClickListener {
//
//            (0..10_000).forEach { i ->
//                publishToTopic("one $i")
//            }
//
//        }

    }

    private fun receivedData(data: String) = lifecycleScope.launch {

        val msg = Gson().fromJson(data, DeviceTemperature::class.java)

        if (msg.data != INVALID_TEMP)
            binding.deviceTemp.text = msg.data.round(1).toString()

    }


    private fun connectToIoT() {

        // Initialize the AWSIotMqttManager with the configuration
        // Initialize the AWSIotMqttManager with the configuration

        mqttManager = AWSIotMqttManager(
            "eu-west-1:c7013970-33e3-4eff-9d4d-78da6ec40db6",
            "a3upko7gc2wjsg-ats.iot.eu-west-1.amazonaws.com"
        )

        cognitoCredentials = CognitoCachingCredentialsProvider(
            context,
            "eu-west-1:c7013970-33e3-4eff-9d4d-78da6ec40db6",
            Regions.EU_WEST_1
        )

//        AWSMobileClient.getInstance().identityId
//
//        val attachPolicyReq = AttachPolicyRequest()
//        attachPolicyReq.policyName = "ESPThemostatPolicy"
//        attachPolicyReq.target = AWSMobileClient.getInstance().identityId
//        val mIotAndroidClient = AWSIotClient(AWSMobileClient.getInstance())
//        mIotAndroidClient.setRegion(Region.getRegion(Regions.EU_WEST_1))
//        mIotAndroidClient.attachPolicy(attachPolicyReq)


        try {
            mqttManager.connect(cognitoCredentials) { status, throwable ->
                Log.d(
                    LOG_TAG,
                    "Connection Status: $status"
                )

                if (status == AWSIotMqttClientStatusCallback.AWSIotMqttClientStatus.Connected) {
                    subscribeToIoTCoreTopic(IOT_CORE_TOPIC)
                }
            }
        } catch (e: Exception) {
            Log.e(LOG_TAG, "Connection error: ", e)
        }


    }

    private fun subscribeToIoTCoreTopic(subTopic: String) {
        try {
            mqttManager.subscribeToTopic(
                subTopic, AWSIotMqttQos.QOS0 /* Quality of Service */
            ) { topic, data ->
                try {
                    val message = String(data, Charset.forName("UTF-8"))

                    receivedData(message)

                    Log.d(LOG_TAG, "Message received: $message")
                } catch (e: UnsupportedEncodingException) {
                    Log.e(LOG_TAG, "Message encoding error: ", e)
                }
            }
        } catch (e: java.lang.Exception) {
            Log.e(LOG_TAG, "Subscription error: ", e)
        }
    }

    private fun publishToTopic(msg: String) {
        try {

            val m = mapOf<String, Any>("status" to "ok", "msg" to msg)
            val data = Gson().toJson(m)

            mqttManager.publishString(data, IOT_CORE_TOPIC, AWSIotMqttQos.QOS0)
        } catch (e: java.lang.Exception) {
            Log.e(LOG_TAG, "Publish error: ", e)
        }
    }

    private fun unsubscribeToTopic() {
        try {
            mqttManager.unsubscribeTopic(IOT_CORE_TOPIC)
        } catch (e: java.lang.Exception) {
            Log.e(LOG_TAG, "Unsubscribe error: ", e)
        }

// You will no longer get messages for "myTopic"
    }

    private fun disconnectIoT() {
        try {
            mqttManager.disconnect()
        } catch (e: java.lang.Exception) {
            Log.e(LOG_TAG, "Disconnect error: ", e)
        }
    }


    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}


data class DeviceTemperature(
    val data: Double,
    val timestamp: Long
)

fun Double.round(decimals: Int): Double {
    var multiplier = 1.0
    repeat(decimals) { multiplier *= 10 }
    return round(this * multiplier) / multiplier
}