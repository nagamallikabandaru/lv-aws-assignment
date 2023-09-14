import boto3
import sys
import os
from datetime import datetime, timedelta , time
import croniter
import pytz


def create_session(aws_access_key_id,aws_secret_access_key):
    try:
        session = boto3.Session(
                                aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key,
                                region_name='ap-south-1')
    except Exception as e:
        print("Unable to create a session")
        session = None
    return session

def get_asg_desired_capacity(session,asg_name):
    autoscaling_client = session.client('autoscaling')
    asg_response = autoscaling_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    return asg_response['AutoScalingGroups'][0]['DesiredCapacity']

def get_instances_across_multi_az(session):
    # Initialize the EC2 client
    ec2_client = session.client('ec2')

    # Get a list of all running EC2 instances
    response = ec2_client.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    # Create a set to store the AZs where instances are running
    azs_running_instances = set()

    # Iterate through the reservations and instances
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            az = instance['Placement']['AvailabilityZone']
            azs_running_instances.add(az)
    # Check if there are instances running in more than one AZ
    if len(azs_running_instances) > 1:
        print("*****************TestCaseA-2********************")
        print("Instances are running across multiple Availability Zones.")
    else:
        print("*****************TestCaseA-2********************")
        print("Instances are running in a single Availability Zone")


def get_scheduled_actions_asg(session,asg_name):
    next_runs = []
    asg_client = session.client('autoscaling')
    response = asg_client.describe_scheduled_actions(AutoScalingGroupName=asg_name)
    for scheduled_action in response['ScheduledUpdateGroupActions']:
        action_name = scheduled_action['ScheduledActionName']
        start_time = scheduled_action['StartTime']
        recurrence = scheduled_action['Recurrence']
        next_run_time = calculate_next_run_time(recurrence,start_time)
        next_runs.append((action_name, next_run_time))
    earliest_next_run = min(next_runs, key=lambda x: x[1])
    print("*****************TestCaseB-1********************")
    print(f"The next scheduled action is '{earliest_next_run[0]}' at '{earliest_next_run[1]}'")
    print("*********************************************")

def calculate_next_run_time(recurrence_schedule, start_time):
    cron = croniter.croniter(recurrence_schedule, start_time)
    next_run_time = cron.get_next(datetime)
    return next_run_time

def get_total_asg_instances(session,asg_name):

    cloudwatch = session.client('cloudwatch')

    # Get the current time in UTC
    current_time = datetime.now(pytz.utc)

    # Calculate the start and end of the current day in UTC
    current_date = current_time.date()
    
    start_time = current_date.strftime("%d/%m/%Y %H:%M:%S")
    end_time = current_time

    try:
        # Retrieve the "GroupTotalInstances" metric data
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/AutoScaling',
                            'MetricName': 'GroupTotalInstances',
                            'Dimensions': [
                                {
                                    'Name': 'AutoScalingGroupName',
                                    'Value': asg_name
                                },
                            ],
                        },
                        'Period': 3600, 
                        'Stat': 'SampleCount',
                    },
                    'ReturnData': True,
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
        )

        # Parse the metric data
        data_points = response['MetricDataResults'][0]['Timestamps']
        sample_counts = response['MetricDataResults'][0]['Values']

        # Calculate the instances launched and terminated
        total_instances_launched = sample_counts[-1] - sample_counts[0]
        total_instances_terminated = total_instances_launched  
        print("**************TestCaseB-2*******************")
        print(f"Total instances launched: {total_instances_launched}")
        print(f"Total instances terminated: {total_instances_terminated}")
        print("*********************************************")
    except Exception as e:
        print("**************TestCaseB-2*******************")
        print(f"Unable to get the asg instance metrics.An error occurred: {str(e)}")    
        print("*********************************************")


def get_running_instances_metrics(session):
    ec2_client = session.client('ec2')
    filters = [
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ]
    try:
        response = ec2_client.describe_instances(Filters=filters)
        if 'Reservations' in response:
            instances = []
            image_ids = []
            vpc_ids = []
            sg_ids = []
            for reservation in response['Reservations']:
                instances.extend(reservation['Instances'])
            if instances:
                for instance in instances:
                    instance_id = instance['InstanceId']
                    print(f"Instance ID: {instance['InstanceId']}, State: {instance['State']['Name']}")
                    vpc_id = response['Reservations'][0]['Instances'][0]['VpcId']
                    print(f"VPC ID: {vpc_id}")
                    vpc_ids.append(vpc_id)
                    security_groups = response['Reservations'][0]['Instances'][0]['SecurityGroups']
                    for sg in security_groups:
                        print(f"Security Group ID: {sg['GroupId']}, Security Group Name: {sg['GroupName']}")
                        sg_ids.append(sg['GroupId'])
                    image_id = instance['ImageId']
                    print(f"IMAGE ID: {image_id}")
                    image_ids.append(image_id)
                # SecuirtyGroup, ImageID and VPCID should be same on ASG running instances
                print("**************TestCaseA-3*******************")
                are_all_same = all(item == image_ids[0] for item in image_ids)
                are_all_same = all(item == vpc_ids[0] for item in vpc_ids)
                are_all_same = all(item == sg_ids[0] for item in sg_ids)

                if are_all_same:
                    print("SecuirtyGroup, ImageID and VPCID are same on the running instances")
                else:
                    print("SecuirtyGroup, ImageID and VPCID are differnt on the running instances")
                return len(instances)
            else:
                print("No running instances found.")
                return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def get_longest_running_instance_on_asg(session,asg_name):
    autoscaling = session.client('autoscaling')
    cloudwatch = session.client('cloudwatch')

    # Get the list of instances in the Auto Scaling Group
    response = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    if not response['AutoScalingGroups']:
        print("Auto Scaling Group not found.")
    else:
        asg = response['AutoScalingGroups'][0]
        instance_ids = [instance['InstanceId'] for instance in asg['Instances']]

        # Create a dictionary to store instance launch times
        instance_launch_times = {}

        # Get the launch times for each instance
        for instance_id in instance_ids:
            response = cloudwatch.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'm1',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/EC2',
                                'MetricName': 'StatusCheckFailed',
                                'Dimensions': [
                                    {
                                        'Name': 'InstanceId',
                                        'Value': instance_id
                                    },
                                ],
                            },
                            'Period': 3600,  # 1-hour interval
                            'Stat': 'SampleCount',
                        },
                        'ReturnData': True,
                    },
                ],
                StartTime=datetime.now() - timedelta(days=365),  # Look back 1 year
                EndTime=datetime.now(),
            )
            if response['MetricDataResults']:
                launch_time = response['MetricDataResults'][0]['Timestamps'][0]
                instance_launch_times[instance_id] = launch_time

        # Calculate the uptime for each instance and find the longest running instance
        current_time = datetime.now()
        longest_running_instance = None
        longest_running_time = timedelta()
        for instance_id, launch_time in instance_launch_times.items():
            uptime = current_time - launch_time
            if uptime > longest_running_time:
                longest_running_time = uptime
                longest_running_instance = instance_id

        # Print the longest running instance and its uptime
        if longest_running_instance:
            print(f"The longest running instance is {longest_running_instance} with uptime: {longest_running_time}")
        else:
            print("No instances found in the Auto Scaling Group.")

def main(argv):
    print(sys.argv)
    if len(sys.argv)>1:
        session = create_session(str(sys.argv[1]),str(sys.argv[2]))
        if session is not None:
            #TestCaseA
            #1- ASG desire running count should be same as running instances. if mismatch fails
            # SecuirtyGroup, ImageID and VPCID should be same on ASG running instances
            asg_desired_count=get_asg_desired_capacity(session,'lv-test-cpu')
            ec2_running_count = get_running_instances_metrics(session)
            try:
                assert asg_desired_count == ec2_running_count
                print("**************TestCaseA-1*******************")
                print("TestCaseA-1 is verified successfully")
                print("*********************************************")
            except AssertionError:
                print("**************TestCaseA-1******************")
                print("DesiredCapacity is not matching the instance running count")
                print("*********************************************")

            #if more than 1 instance running on ASG, then ec2 instance should on available and distributed on multiple availibity zone.
            get_instances_across_multi_az(session)
            
            #Findout uptime of ASG running instances and get the longest running instance.
            get_longest_running_instance_on_asg(session,'lv-test-cpu')
            
            #TestCaseB
            #Find the Scheduled actions of given ASG which is going to run next and calcalate elapsed in hh:mm:ss from current time.
            get_scheduled_actions_asg(session,'lv-test-cpu')
            #Calculate total number instances lunched and terminated on current day for the given ASG.
            get_total_asg_instances(session,'lv-test-cpu')
    else:
        print("Please pass correct arguments:access_key and secret_key")


if __name__ == "__main__":
    main(sys.argv)